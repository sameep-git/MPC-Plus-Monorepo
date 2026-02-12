using System.IO.Compression;
using Api.Models;
using Api.Repositories;
using Api.Repositories.Abstractions;
using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;

namespace Api.Services;

public class ReportService : IReportService
{
    private readonly IBeamRepository _beamRepository;
    private readonly IGeoCheckRepository _geoCheckRepository;
    private readonly IMachineRepository _machineRepository;
    private readonly IThresholdRepository _thresholdRepository;

    public ReportService(
        IBeamRepository beamRepository,
        IGeoCheckRepository geoCheckRepository,
        IMachineRepository machineRepository,
        IThresholdRepository thresholdRepository)
    {
        _beamRepository = beamRepository;
        _geoCheckRepository = geoCheckRepository;
        _machineRepository = machineRepository;
        _thresholdRepository = thresholdRepository;
    }

    public async Task<(byte[] Data, string ContentType, string FileName)> GenerateReportAsync(ReportRequest request, CancellationToken cancellationToken = default)
    {
        // 1. Fetch Machine Details
        var machine = await _machineRepository.GetByIdAsync(request.MachineId, cancellationToken);
        var machineName = machine?.Name ?? "Unknown Machine";
        var safeMachineName = machineName.Replace(" ", "_");

        // 2. Parse SelectedChecks
        Console.WriteLine($"[ReportService] SelectedChecks: [{string.Join(", ", request.SelectedChecks)}]");

        var selectedBeamTypes = request.SelectedChecks
            .Where(c => c.StartsWith("beam-", StringComparison.OrdinalIgnoreCase))
            .Select(c => c.Substring(5))
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        var selectedGeoTypes = request.SelectedChecks
            .Where(c => c.StartsWith("geo-", StringComparison.OrdinalIgnoreCase))
            .Select(c => c.Substring(4))
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        Console.WriteLine($"[ReportService] Parsed beam types count: {selectedBeamTypes.Count}, types: [{string.Join(", ", selectedBeamTypes)}]");
        Console.WriteLine($"[ReportService] Parsed geo types: [{string.Join(", ", selectedGeoTypes)}]");

        // 3. Fetch ALL data for the full range once
        var searchEndDate = request.EndDate.Date.AddDays(1);

        var allBeams = await _beamRepository.GetAllAsync(
            machineId: request.MachineId,
            startDate: request.StartDate,
            endDate: searchEndDate,
            cancellationToken: cancellationToken);

        Console.WriteLine($"[ReportService] Fetched {allBeams.Count} beams for range {request.StartDate:yyyy-MM-dd} to {searchEndDate:yyyy-MM-dd}");

        var allGeoChecks = await _geoCheckRepository.GetAllAsync(
            machineId: request.MachineId,
            startDate: request.StartDate,
            endDate: searchEndDate,
            cancellationToken: cancellationToken);

        Console.WriteLine($"[ReportService] Fetched {allGeoChecks.Count} geoChecks for range {request.StartDate:yyyy-MM-dd} to {searchEndDate:yyyy-MM-dd}");

        // 3b. Fetch thresholds from the database
        var thresholds = await _thresholdRepository.GetAllAsync(cancellationToken);
        Console.WriteLine($"[ReportService] Fetched {thresholds.Count} thresholds from database");

        // 4. Filter data by selected checks
        List<Beam> filteredBeams;
        if (selectedBeamTypes.Count == 0)
        {
            filteredBeams = allBeams.OrderBy(b => b.Date).ThenBy(b => b.Type).ToList();
        }
        else
        {
            filteredBeams = allBeams
                .Where(b => selectedBeamTypes.Contains(b.Type ?? ""))
                .OrderBy(b => b.Date)
                .ThenBy(b => b.Type)
                .ToList();
        }

        var filteredGeoChecks = allGeoChecks.OrderBy(g => g.Date).ToList();
        var showGeoChecks = selectedGeoTypes.Count > 0;

        // 5. Group data by CALENDAR DAY (strip time component)
        var beamsByDay = filteredBeams
            .GroupBy(b => b.Date.Date)
            .ToDictionary(g => g.Key, g => g.ToList());

        var geoByDay = filteredGeoChecks
            .GroupBy(g => g.Date.Date)
            .ToDictionary(g => g.Key, g => g.ToList());

        // Collect all unique days that have data, filtered to the requested range
        IEnumerable<DateTime> geoDays = showGeoChecks ? geoByDay.Keys : Enumerable.Empty<DateTime>();
        var allDays = beamsByDay.Keys
            .Union(geoDays)
            .Where(d => d.Date >= request.StartDate.Date && d.Date <= request.EndDate.Date)
            .OrderBy(d => d)
            .ToList();

        Console.WriteLine($"[ReportService] Days with data: {allDays.Count} [{string.Join(", ", allDays.Select(d => d.ToString("yyyy-MM-dd")))}]");

        if (allDays.Count == 0)
        {
            // Generate an empty report for the range so the user gets feedback
            var emptyPdf = GenerateSingleDayPdf(machineName, request.StartDate, request.EndDate,
                new List<Beam>(), new List<GeoCheck>(), selectedGeoTypes, false, thresholds);
            var emptyFileName = $"MPC_Report_{safeMachineName}_{request.StartDate:yyyyMMdd}.pdf";
            return (emptyPdf, "application/pdf", emptyFileName);
        }

        if (allDays.Count == 1)
        {
            // Single day — return PDF directly
            var day = allDays[0];
            var dayBeams = beamsByDay.GetValueOrDefault(day, new List<Beam>());
            var dayGeo = geoByDay.GetValueOrDefault(day, new List<GeoCheck>());

            var pdfBytes = GenerateSingleDayPdf(machineName, day, day,
                dayBeams, dayGeo, selectedGeoTypes, showGeoChecks, thresholds);

            var fileName = $"MPC_Report_{safeMachineName}_{day:yyyyMMdd}.pdf";
            Console.WriteLine($"[ReportService] Single day PDF generated. Size: {pdfBytes.Length} bytes.");
            return (pdfBytes, "application/pdf", fileName);
        }

        // Multiple days — generate per-day PDFs and bundle into ZIP
        Console.WriteLine($"[ReportService] Generating ZIP with {allDays.Count} daily reports.");
        using var zipStream = new MemoryStream();
        using (var archive = new ZipArchive(zipStream, ZipArchiveMode.Create, leaveOpen: true))
        {
            foreach (var day in allDays)
            {
                var dayBeams = beamsByDay.GetValueOrDefault(day, new List<Beam>());
                var dayGeo = geoByDay.GetValueOrDefault(day, new List<GeoCheck>());

                var pdfBytes = GenerateSingleDayPdf(machineName, day, day,
                    dayBeams, dayGeo, selectedGeoTypes, showGeoChecks, thresholds);

                var entryName = $"MPC_Report_{safeMachineName}_{day:yyyyMMdd}.pdf";
                var entry = archive.CreateEntry(entryName, CompressionLevel.Fastest);
                using var entryStream = entry.Open();
                await entryStream.WriteAsync(pdfBytes, cancellationToken);
            }
        }

        var zipBytes = zipStream.ToArray();
        var zipFileName = $"MPC_Reports_{safeMachineName}_{request.StartDate:yyyyMMdd}_to_{request.EndDate:yyyyMMdd}.zip";
        Console.WriteLine($"[ReportService] ZIP generated. Size: {zipBytes.Length} bytes, {allDays.Count} PDFs.");
        return (zipBytes, "application/zip", zipFileName);
    }

    /// <summary>
    /// Generates a PDF report for a single day's worth of data.
    /// </summary>
    private byte[] GenerateSingleDayPdf(
        string machineName,
        DateTime startDate,
        DateTime endDate,
        List<Beam> beams,
        List<GeoCheck> geoChecks,
        HashSet<string> selectedGeoTypes,
        bool showGeoChecks,
        IReadOnlyList<Threshold> thresholds)
    {
        var document = Document.Create(container =>
        {
            container.Page(page =>
            {
                page.Size(PageSizes.A4);
                page.Margin(2, Unit.Centimetre);
                page.PageColor(Colors.White);
                page.DefaultTextStyle(x => x.FontSize(10).FontFamily(Fonts.Arial));

                page.Header().Element(header => ComposeHeader(header, machineName, startDate, endDate));
                page.Content().Element(content => ComposeContent(content, beams, geoChecks, selectedGeoTypes, showGeoChecks, thresholds));
                page.Footer().Element(ComposeFooter);
            });
        });

        return document.GeneratePdf();
    }

    private void ComposeHeader(IContainer container, string machineName, DateTime startDate, DateTime endDate)
    {
        container.Row(row =>
        {
            row.RelativeItem().Column(column =>
            {
                column.Item().Text("MPC+").FontSize(24).SemiBold().FontColor(Colors.Purple.Medium);
                column.Item().Text("Machine Performance Check").FontSize(10).FontColor(Colors.Grey.Medium);
            });

            row.RelativeItem().AlignRight().Column(column =>
            {
                column.Item().Text("Session Report").FontSize(20).SemiBold();
                column.Item().Text($"Machine: {machineName}").FontSize(12);
                column.Item().Text($"Date Range: {startDate:MM/dd/yyyy} - {endDate:MM/dd/yyyy}").FontSize(10);
                column.Item().Text($"Generated: {DateTime.Now:g}").FontSize(9).FontColor(Colors.Grey.Medium);
            });
        });
    }

    private void ComposeContent(IContainer container, List<Beam> beams, List<GeoCheck> geoChecks,
        HashSet<string> selectedGeoTypes, bool showGeoChecks, IReadOnlyList<Threshold> thresholds)
    {
        container.PaddingVertical(0.5f, Unit.Centimetre).Column(column =>
        {
            // Overview Section
            column.Item().Element(c => ComposeOverview(c, beams, geoChecks, showGeoChecks, thresholds));

            column.Item().PaddingVertical(0.3f, Unit.Centimetre).LineHorizontal(1).LineColor(Colors.Grey.Lighten2);

            // Beam Checks Section
            if (beams.Count > 0)
            {
                column.Item().PaddingTop(0.5f, Unit.Centimetre).Text("Beam Checks").FontSize(16).SemiBold();
                
                foreach (var beam in beams)
                {
                    column.Item().Element(c => ComposeBeamSection(c, beam, thresholds));
                }
            }

            // Geometry Checks Section
            if (showGeoChecks && geoChecks.Count > 0)
            {
                column.Item().PaddingTop(0.5f, Unit.Centimetre).LineHorizontal(1).LineColor(Colors.Grey.Lighten2);
                column.Item().PaddingTop(0.5f, Unit.Centimetre).Text("Geometry Checks").FontSize(16).SemiBold();
                
                foreach (var geo in geoChecks)
                {
                    column.Item().Element(c => ComposeGeoSection(c, geo, selectedGeoTypes, thresholds));
                }
            }
        });
    }

    private void ComposeOverview(IContainer container, List<Beam> beams, List<GeoCheck> geoChecks,
        bool showGeoChecks, IReadOnlyList<Threshold> thresholds)
    {
        // Count passed beams by checking if all metrics pass against thresholds
        var passedBeams = beams.Count(b => IsBeamPassing(b, thresholds));
        
        var totalBeams = beams.Count;
        var geoCount = showGeoChecks ? geoChecks.Count : 0;
        var totalChecks = totalBeams + geoCount;
        var passedGeo = showGeoChecks ? geoChecks.Count(g => IsGeoPassing(g, thresholds)) : 0;
        var passedTotal = passedBeams + passedGeo;

        container.Column(column =>
        {
            column.Item().Text("Overview").FontSize(16).SemiBold();
            column.Item().PaddingTop(5).Row(row =>
            {
                row.RelativeItem().Column(col =>
                {
                    col.Item().Text($"Total Checks: {totalChecks}");
                    col.Item().Text($"Beam Checks: {totalBeams}");
                    if (showGeoChecks) col.Item().Text($"Geometry Checks: {geoCount}");
                });
                row.RelativeItem().Column(col =>
                {
                    var statusColor = passedTotal == totalChecks ? Colors.Green.Medium : Colors.Orange.Medium;
                    col.Item().Text($"{passedTotal}/{totalChecks} Within Thresholds").FontColor(statusColor).SemiBold();
                });
            });
        });
    }

    /// <summary>
    /// Finds a threshold value from the database for a given beam/geo check.
    /// Returns null if no threshold is configured.
    /// </summary>
    private double? FindThreshold(IReadOnlyList<Threshold> thresholds, string machineId,
        string checkType, string? beamVariant, string metricType)
    {
        var threshold = thresholds.FirstOrDefault(t =>
            t.MachineId == machineId &&
            string.Equals(t.CheckType, checkType, StringComparison.OrdinalIgnoreCase) &&
            string.Equals(t.BeamVariant, beamVariant, StringComparison.OrdinalIgnoreCase) &&
            string.Equals(t.MetricType, metricType, StringComparison.OrdinalIgnoreCase));

        return threshold?.Value;
    }

    /// <summary>
    /// Determines if a metric passes. If no threshold exists, it passes by default.
    /// </summary>
    private bool IsMetricPassing(double? value, double? thresholdValue)
    {
        if (!value.HasValue) return true;
        if (!thresholdValue.HasValue) return true; // No threshold configured = pass
        return Math.Abs(value.Value) <= thresholdValue.Value;
    }

    // Helper to determine if a beam passes based on metric values and dynamic thresholds
    private bool IsBeamPassing(Beam beam, IReadOnlyList<Threshold> thresholds)
    {
        var outputThreshold = FindThreshold(thresholds, beam.MachineId, "beam", beam.Type, "Relative Output");
        var uniformityThreshold = FindThreshold(thresholds, beam.MachineId, "beam", beam.Type, "Relative Uniformity");
        var centerThreshold = FindThreshold(thresholds, beam.MachineId, "beam", beam.Type, "Center Shift");

        bool outputPass = IsMetricPassing(beam.RelOutput, outputThreshold);
        bool uniformityPass = IsMetricPassing(beam.RelUniformity, uniformityThreshold);
        bool centerPass = IsMetricPassing(beam.CenterShift, centerThreshold);
        
        return outputPass && uniformityPass && centerPass;
    }

    // Helper to determine if a geo check passes overall based on dynamic thresholds
    private bool IsGeoPassing(GeoCheck geo, IReadOnlyList<Threshold> thresholds)
    {
        bool pass = true;
        pass &= IsMetricPassing(geo.IsoCenterSize, FindThreshold(thresholds, geo.MachineId, "geo", null, "IsoCenter Size"));
        pass &= IsMetricPassing(geo.IsoCenterMVOffset, FindThreshold(thresholds, geo.MachineId, "geo", null, "IsoCenter MV Offset"));
        pass &= IsMetricPassing(geo.IsoCenterKVOffset, FindThreshold(thresholds, geo.MachineId, "geo", null, "IsoCenter kV Offset"));
        pass &= IsMetricPassing(geo.GantryAbsolute, FindThreshold(thresholds, geo.MachineId, "geo", null, "Gantry Absolute"));
        pass &= IsMetricPassing(geo.GantryRelative, FindThreshold(thresholds, geo.MachineId, "geo", null, "Gantry Relative"));
        pass &= IsMetricPassing(geo.CouchMaxPositionError, FindThreshold(thresholds, geo.MachineId, "geo", null, "Couch Max Position Error"));
        pass &= IsMetricPassing(geo.CollimationRotationOffset, FindThreshold(thresholds, geo.MachineId, "geo", null, "Collimation Rotation"));

        // MLC leaf positions
        var mlcThreshold = FindThreshold(thresholds, geo.MachineId, "geo", null, "mlc_leaf_position");
        if (mlcThreshold.HasValue)
        {
            if (geo.MLCLeavesA != null)
                pass &= geo.MLCLeavesA.Values.All(v => Math.Abs(v) <= mlcThreshold.Value);
            if (geo.MLCLeavesB != null)
                pass &= geo.MLCLeavesB.Values.All(v => Math.Abs(v) <= mlcThreshold.Value);
        }

        // MLC backlash
        var backlashThreshold = FindThreshold(thresholds, geo.MachineId, "geo", null, "mlc_backlash");
        if (backlashThreshold.HasValue)
        {
            if (geo.MLCBacklashA != null)
                pass &= geo.MLCBacklashA.Values.All(v => Math.Abs(v) <= backlashThreshold.Value);
            if (geo.MLCBacklashB != null)
                pass &= geo.MLCBacklashB.Values.All(v => Math.Abs(v) <= backlashThreshold.Value);
        }

        return pass;
    }

    private void ComposeBeamSection(IContainer container, Beam beam, IReadOnlyList<Threshold> thresholds)
    {
        // Look up dynamic thresholds
        var outputThreshold = FindThreshold(thresholds, beam.MachineId, "beam", beam.Type, "Relative Output");
        var uniformityThreshold = FindThreshold(thresholds, beam.MachineId, "beam", beam.Type, "Relative Uniformity");
        var centerThreshold = FindThreshold(thresholds, beam.MachineId, "beam", beam.Type, "Center Shift");

        // Determine pass/fail based on actual metric values
        var isPass = IsBeamPassing(beam, thresholds);
        var statusColor = isPass ? Colors.Green.Medium : Colors.Red.Medium;
        var statusText = isPass ? "PASS" : "FAIL";
        
        // Use Timestamp if available, otherwise fall back to Date, convert to local time
        var displayTime = (beam.Timestamp ?? beam.Date).ToLocalTime();

        container.PaddingTop(0.4f, Unit.Centimetre).Column(column =>
        {
            // Header with beam type and status
            column.Item().Row(row =>
            {
                row.RelativeItem().Text($"Beam Check ({beam.Type})").FontSize(12).SemiBold();
                row.ConstantItem(60).AlignRight().Text(statusText).FontSize(11).SemiBold().FontColor(statusColor);
            });
            column.Item().Text($"Date: {displayTime:MM/dd/yyyy h:mm tt}").FontSize(9).FontColor(Colors.Grey.Medium);

            // Metrics Table
            column.Item().PaddingTop(0.2f, Unit.Centimetre).Table(table =>
            {
                table.ColumnsDefinition(columns =>
                {
                    columns.RelativeColumn(3); // Metric
                    columns.RelativeColumn(2); // Value
                    columns.RelativeColumn(2); // Threshold
                    columns.RelativeColumn(1); // Status
                });

                // Header
                table.Header(header =>
                {
                    header.Cell().Element(HeaderCellStyle).Text("Metric");
                    header.Cell().Element(HeaderCellStyle).Text("Value");
                    header.Cell().Element(HeaderCellStyle).Text("Threshold");
                    header.Cell().Element(HeaderCellStyle).Text("Status");

                    static IContainer HeaderCellStyle(IContainer c) =>
                        c.BorderBottom(1).BorderColor(Colors.Grey.Lighten2).Padding(4).DefaultTextStyle(x => x.SemiBold().FontSize(9));
                });

                // Relative Output
                AddMetricRow(table, "Relative Output", 
                    beam.RelOutput, outputThreshold, "%");

                // Relative Uniformity
                AddMetricRow(table, "Relative Uniformity", 
                    beam.RelUniformity, uniformityThreshold, "%");

                // Center Shift
                AddMetricRow(table, "Center Shift", 
                    beam.CenterShift, centerThreshold, "mm");
            });
        });
    }

    private void AddMetricRow(TableDescriptor table, string name, double? value, double? thresholdValue, string unit)
    {
        var isPass = IsMetricPassing(value, thresholdValue);
        var statusColor = isPass ? Colors.Green.Medium : Colors.Red.Medium;
        var statusText = isPass ? "PASS" : "FAIL";
        var valueStr = value.HasValue ? $"{value.Value:F3}" : "-";
        var thresholdStr = thresholdValue.HasValue ? $"± {thresholdValue.Value:F2} {unit}" : "N/A";

        table.Cell().Element(DataCellStyle).Text(name);
        table.Cell().Element(DataCellStyle).Text(valueStr);
        table.Cell().Element(DataCellStyle).Text(thresholdStr);
        table.Cell().Element(DataCellStyle).Text(statusText).FontColor(statusColor);
    }

    private static IContainer DataCellStyle(IContainer c) =>
        c.BorderBottom(1).BorderColor(Colors.Grey.Lighten4).Padding(4).DefaultTextStyle(x => x.FontSize(9));

    // Helper to add a geo metric row with dynamic threshold lookup
    private void AddGeoMetricRow(TableDescriptor table, string name, double? value, string unit, double? thresholdValue)
    {
        var isPass = IsMetricPassing(value, thresholdValue);
        var statusColor = isPass ? Colors.Green.Medium : Colors.Red.Medium;
        var statusText = isPass ? "PASS" : "FAIL";
        var valueStr = value.HasValue ? $"{value.Value:F2} {unit}" : "-";
        var thresholdStr = thresholdValue.HasValue ? $"± {thresholdValue.Value:F2} {unit}" : "N/A";

        table.Cell().Element(DataCellStyle).Text(name);
        table.Cell().Element(DataCellStyle).Text(valueStr);
        table.Cell().Element(DataCellStyle).Text(thresholdStr);
        table.Cell().Element(DataCellStyle).Text(statusText).FontColor(statusColor);
    }

    // Helper to add a summary pass/fail row for a group of leaves (no individual value shown)
    private void AddGroupPassFailRow(TableDescriptor table, string name, bool isPass, double? thresholdValue, string unit)
    {
        var statusColor = isPass ? Colors.Green.Medium : Colors.Red.Medium;
        var statusText = isPass ? "PASS" : "FAIL";
        var thresholdStr = thresholdValue.HasValue ? $"± {thresholdValue.Value:F2} {unit}" : "N/A";

        table.Cell().Element(DataCellStyle).Text(name);
        table.Cell().Element(DataCellStyle).Text(""); // No individual value for group summary
        table.Cell().Element(DataCellStyle).Text(thresholdStr);
        table.Cell().Element(DataCellStyle).Text(statusText).FontColor(statusColor);
    }


    private void ComposeGeoSection(IContainer container, GeoCheck geo, HashSet<string> selectedGeoTypes,
        IReadOnlyList<Threshold> thresholds)
    {
        // Determine overall geo check pass/fail using dynamic thresholds
        bool isOverallPass = IsGeoPassing(geo, thresholds);
        
        var overallStatusColor = isOverallPass ? Colors.Green.Medium : Colors.Red.Medium;
        var overallStatusText = isOverallPass ? "PASS" : "FAIL";

        container.PaddingTop(0.4f, Unit.Centimetre).Column(column =>
        {
            // Use Timestamp if available, otherwise fall back to Date, convert to local time
            var geoDisplayTime = (geo.Timestamp ?? geo.Date).ToLocalTime();
            
            // Header with overall status (no N/A for type)
            column.Item().Row(row =>
            {
                row.RelativeItem().Text("Geometry Check").FontSize(12).SemiBold();
                row.ConstantItem(60).AlignRight().Text(overallStatusText).FontSize(11).SemiBold().FontColor(overallStatusColor);
            });
            column.Item().Text($"Date: {geoDisplayTime:MM/dd/yyyy h:mm tt}").FontSize(9).FontColor(Colors.Grey.Medium);

            // IsoCenter
            if (selectedGeoTypes.Contains("isocenter") || selectedGeoTypes.Count == 0)
            {
                column.Item().PaddingTop(0.2f, Unit.Centimetre).Text("Isocenter").FontSize(10).SemiBold();
                column.Item().Table(table =>
                {
                    table.ColumnsDefinition(columns =>
                    {
                        columns.RelativeColumn(3); // Metric
                        columns.RelativeColumn(2); // Value
                        columns.RelativeColumn(2); // Threshold
                        columns.RelativeColumn(1); // Status
                    });

                    AddGeoMetricRow(table, "Size", geo.IsoCenterSize, "mm",
                        FindThreshold(thresholds, geo.MachineId, "geo", null, "IsoCenter Size"));
                    if (geo.IsoCenterMVOffset.HasValue)
                        AddGeoMetricRow(table, "MV Offset", geo.IsoCenterMVOffset, "mm",
                            FindThreshold(thresholds, geo.MachineId, "geo", null, "IsoCenter MV Offset"));
                    if (geo.IsoCenterKVOffset.HasValue)
                        AddGeoMetricRow(table, "kV Offset", geo.IsoCenterKVOffset, "mm",
                            FindThreshold(thresholds, geo.MachineId, "geo", null, "IsoCenter kV Offset"));
                });
            }

            // Gantry
            if (selectedGeoTypes.Contains("gantry") || selectedGeoTypes.Count == 0)
            {
                if (geo.GantryAbsolute.HasValue || geo.GantryRelative.HasValue)
                {
                    column.Item().PaddingTop(0.2f, Unit.Centimetre).Text("Gantry").FontSize(10).SemiBold();
                    column.Item().Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.RelativeColumn(3);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(1);
                        });

                        if (geo.GantryAbsolute.HasValue)
                            AddGeoMetricRow(table, "Absolute", geo.GantryAbsolute, "°",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "Gantry Absolute"));
                        if (geo.GantryRelative.HasValue)
                            AddGeoMetricRow(table, "Relative", geo.GantryRelative, "°",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "Gantry Relative"));
                    });
                }
            }

            // Couch
            if (selectedGeoTypes.Contains("couch") || selectedGeoTypes.Count == 0)
            {
                if (geo.CouchMaxPositionError.HasValue)
                {
                    column.Item().PaddingTop(0.2f, Unit.Centimetre).Text("Couch").FontSize(10).SemiBold();
                    column.Item().Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.RelativeColumn(3);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(1);
                        });

                        AddGeoMetricRow(table, "Max Position Error", geo.CouchMaxPositionError, "mm",
                            FindThreshold(thresholds, geo.MachineId, "geo", null, "Couch Max Position Error"));
                    });
                }
            }

            // Collimation
            if (selectedGeoTypes.Contains("collimation") || selectedGeoTypes.Count == 0)
            {
                if (geo.CollimationRotationOffset.HasValue)
                {
                    column.Item().PaddingTop(0.2f, Unit.Centimetre).Text("Collimation").FontSize(10).SemiBold();
                    column.Item().Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.RelativeColumn(3);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(1);
                        });

                        AddGeoMetricRow(table, "Rotation Offset", geo.CollimationRotationOffset, "°",
                            FindThreshold(thresholds, geo.MachineId, "geo", null, "Collimation Rotation"));
                    });
                }
            }

            // MLC
            if (selectedGeoTypes.Contains("mlc-offsets") || selectedGeoTypes.Contains("mlc-a") || selectedGeoTypes.Contains("mlc-b") || selectedGeoTypes.Count == 0)
            {
                bool hasMlcData = geo.MaxOffsetA.HasValue || geo.MaxOffsetB.HasValue || geo.MeanOffsetA.HasValue || geo.MeanOffsetB.HasValue
                    || (geo.MLCLeavesA != null && geo.MLCLeavesA.Count > 0) || (geo.MLCLeavesB != null && geo.MLCLeavesB.Count > 0);

                if (hasMlcData)
                {
                    column.Item().PaddingTop(0.2f, Unit.Centimetre).Text("MLC").FontSize(10).SemiBold();
                    column.Item().Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.RelativeColumn(3);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(1);
                        });

                        var mlcThreshold = FindThreshold(thresholds, geo.MachineId, "geo", null, "mlc_leaf_position");

                        if (geo.MaxOffsetA.HasValue)
                            AddGeoMetricRow(table, "Maximal Offset Leaves A", geo.MaxOffsetA, "mm", mlcThreshold);
                        if (geo.MaxOffsetB.HasValue)
                            AddGeoMetricRow(table, "Maximal Offset Leaves B", geo.MaxOffsetB, "mm", mlcThreshold);
                        if (geo.MeanOffsetA.HasValue)
                            AddGeoMetricRow(table, "Mean Offset Leaves A", geo.MeanOffsetA, "mm", mlcThreshold);
                        if (geo.MeanOffsetB.HasValue)
                            AddGeoMetricRow(table, "Mean Offset Leaves B", geo.MeanOffsetB, "mm", mlcThreshold);

                        // Leaves A overall pass/fail (check if all individual leaves are within threshold)
                        if (geo.MLCLeavesA != null && geo.MLCLeavesA.Count > 0)
                        {
                            bool leavesAPass = !mlcThreshold.HasValue || geo.MLCLeavesA.Values.All(v => Math.Abs(v) <= mlcThreshold.Value);
                            AddGroupPassFailRow(table, "Leaves A", leavesAPass, mlcThreshold, "mm");
                        }

                        // Leaves B overall pass/fail
                        if (geo.MLCLeavesB != null && geo.MLCLeavesB.Count > 0)
                        {
                            bool leavesBPass = !mlcThreshold.HasValue || geo.MLCLeavesB.Values.All(v => Math.Abs(v) <= mlcThreshold.Value);
                            AddGroupPassFailRow(table, "Leaves B", leavesBPass, mlcThreshold, "mm");
                        }
                    });
                }
            }

            // MLC Reproducibility (Backlash)
            if (selectedGeoTypes.Contains("backlash-a") || selectedGeoTypes.Contains("backlash-b") || selectedGeoTypes.Count == 0)
            {
                bool hasBacklashData = geo.MLCBacklashMaxA.HasValue || geo.MLCBacklashMaxB.HasValue || geo.MLCBacklashMeanA.HasValue || geo.MLCBacklashMeanB.HasValue
                    || (geo.MLCBacklashA != null && geo.MLCBacklashA.Count > 0) || (geo.MLCBacklashB != null && geo.MLCBacklashB.Count > 0);

                if (hasBacklashData)
                {
                    column.Item().PaddingTop(0.2f, Unit.Centimetre).Text("MLC Reproducibility").FontSize(10).SemiBold();
                    column.Item().Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.RelativeColumn(3);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(1);
                        });

                        var backlashThreshold = FindThreshold(thresholds, geo.MachineId, "geo", null, "mlc_backlash");

                        if (geo.MLCBacklashMaxA.HasValue)
                            AddGeoMetricRow(table, "Maximal Reproducibility Leaves A", geo.MLCBacklashMaxA, "mm", backlashThreshold);
                        if (geo.MLCBacklashMaxB.HasValue)
                            AddGeoMetricRow(table, "Maximal Reproducibility Leaves B", geo.MLCBacklashMaxB, "mm", backlashThreshold);
                        if (geo.MLCBacklashMeanA.HasValue)
                            AddGeoMetricRow(table, "Mean Reproducibility Leaves A", geo.MLCBacklashMeanA, "mm", backlashThreshold);
                        if (geo.MLCBacklashMeanB.HasValue)
                            AddGeoMetricRow(table, "Mean Reproducibility Leaves B", geo.MLCBacklashMeanB, "mm", backlashThreshold);

                        // Leaves A overall pass/fail
                        if (geo.MLCBacklashA != null && geo.MLCBacklashA.Count > 0)
                        {
                            bool backlashAPass = !backlashThreshold.HasValue || geo.MLCBacklashA.Values.All(v => Math.Abs(v) <= backlashThreshold.Value);
                            AddGroupPassFailRow(table, "Leaves A", backlashAPass, backlashThreshold, "mm");
                        }

                        // Leaves B overall pass/fail
                        if (geo.MLCBacklashB != null && geo.MLCBacklashB.Count > 0)
                        {
                            bool backlashBPass = !backlashThreshold.HasValue || geo.MLCBacklashB.Values.All(v => Math.Abs(v) <= backlashThreshold.Value);
                            AddGroupPassFailRow(table, "Leaves B", backlashBPass, backlashThreshold, "mm");
                        }
                    });
                }
            }

            // Jaws
            if (selectedGeoTypes.Contains("jaws") || selectedGeoTypes.Count == 0)
            {
                if (geo.JawX1.HasValue || geo.JawX2.HasValue || geo.JawY1.HasValue || geo.JawY2.HasValue)
                {
                    column.Item().PaddingTop(0.2f, Unit.Centimetre).Text("Jaws").FontSize(10).SemiBold();
                    column.Item().Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.RelativeColumn(3);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(1);
                        });

                        if (geo.JawX1.HasValue)
                            AddGeoMetricRow(table, "Jaw X1", geo.JawX1, "mm",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "JawX1"));
                        if (geo.JawX2.HasValue)
                            AddGeoMetricRow(table, "Jaw X2", geo.JawX2, "mm",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "JawX2"));
                        if (geo.JawY1.HasValue)
                            AddGeoMetricRow(table, "Jaw Y1", geo.JawY1, "mm",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "JawY1"));
                        if (geo.JawY2.HasValue)
                            AddGeoMetricRow(table, "Jaw Y2", geo.JawY2, "mm",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "JawY2"));
                    });
                }
            }

            // Jaws Parallelism
            if (selectedGeoTypes.Contains("jaws-parallelism") || selectedGeoTypes.Count == 0)
            {
                if (geo.JawParallelismX1.HasValue || geo.JawParallelismX2.HasValue || geo.JawParallelismY1.HasValue || geo.JawParallelismY2.HasValue)
                {
                    column.Item().PaddingTop(0.2f, Unit.Centimetre).Text("Jaws Parallelism").FontSize(10).SemiBold();
                    column.Item().Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.RelativeColumn(3);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(2);
                            columns.RelativeColumn(1);
                        });

                        if (geo.JawParallelismX1.HasValue)
                            AddGeoMetricRow(table, "Parallelism X1", geo.JawParallelismX1, "mm",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "ParallelismX1"));
                        if (geo.JawParallelismX2.HasValue)
                            AddGeoMetricRow(table, "Parallelism X2", geo.JawParallelismX2, "mm",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "ParallelismX2"));
                        if (geo.JawParallelismY1.HasValue)
                            AddGeoMetricRow(table, "Parallelism Y1", geo.JawParallelismY1, "mm",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "ParallelismY1"));
                        if (geo.JawParallelismY2.HasValue)
                            AddGeoMetricRow(table, "Parallelism Y2", geo.JawParallelismY2, "mm",
                                FindThreshold(thresholds, geo.MachineId, "geo", null, "ParallelismY2"));
                    });
                }
            }
        });
    }

    private void ComposeFooter(IContainer container)
    {
        container.AlignCenter().Text(x =>
        {
            x.CurrentPageNumber();
            x.Span(" of ");
            x.TotalPages();
        });
    }
}
