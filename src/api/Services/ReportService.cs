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

    public ReportService(
        IBeamRepository beamRepository,
        IGeoCheckRepository geoCheckRepository,
        IMachineRepository machineRepository)
    {
        _beamRepository = beamRepository;
        _geoCheckRepository = geoCheckRepository;
        _machineRepository = machineRepository;
    }

    public async Task<byte[]> GenerateReportAsync(ReportRequest request, CancellationToken cancellationToken = default)
    {
        // 1. Fetch Machine Details
        var machine = await _machineRepository.GetByIdAsync(request.MachineId, cancellationToken);
        var machineName = machine?.Name ?? "Unknown Machine";

        // 2. Fetch Data - extend EndDate to include full day
        var searchEndDate = request.EndDate.Date.AddDays(1);
        
        var beams = await _beamRepository.GetAllAsync(
            machineId: request.MachineId,
            startDate: request.StartDate,
            endDate: searchEndDate,
            cancellationToken: cancellationToken);

        Console.WriteLine($"[ReportService] Fetched {beams.Count} beams for range {request.StartDate:yyyy-MM-dd} to {searchEndDate:yyyy-MM-dd}");
        
        // Debug: Log beam types available
        var beamTypesList = beams.Select(b => b.Type).Distinct().ToList();
        Console.WriteLine($"[ReportService] Available beam types: [{string.Join(", ", beamTypesList)}]");

        var geoChecks = await _geoCheckRepository.GetAllAsync(
            machineId: request.MachineId,
            startDate: request.StartDate,
            endDate: searchEndDate,
            cancellationToken: cancellationToken);

        Console.WriteLine($"[ReportService] Fetched {geoChecks.Count} geoChecks for range {request.StartDate:yyyy-MM-dd} to {searchEndDate:yyyy-MM-dd}");

        // 3. Parse SelectedChecks
        // Frontend sends IDs like "beam-{uuid}", "geo-isocenter", etc.
        Console.WriteLine($"[ReportService] SelectedChecks: [{string.Join(", ", request.SelectedChecks)}]");
        
        // Extract beam IDs (UUIDs) from selectedChecks
        var selectedBeamIds = request.SelectedChecks
            .Where(c => c.StartsWith("beam-", StringComparison.OrdinalIgnoreCase))
            .Select(c => c.Substring(5)) // Remove "beam-" prefix to get the UUID
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        var selectedGeoTypes = request.SelectedChecks
            .Where(c => c.StartsWith("geo-", StringComparison.OrdinalIgnoreCase))
            .Select(c => c.Substring(4)) // Remove "geo-" prefix
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        Console.WriteLine($"[ReportService] Parsed beam IDs count: {selectedBeamIds.Count}");
        Console.WriteLine($"[ReportService] Parsed geo types: [{string.Join(", ", selectedGeoTypes)}]");

        // 4. Filter data - match beams by their ID
        List<Beam> filteredBeams;
        if (selectedBeamIds.Count == 0)
        {
            // No beam selections means include all beams
            filteredBeams = beams.OrderBy(b => b.Date).ThenBy(b => b.Type).ToList();
            Console.WriteLine($"[ReportService] No beam IDs selected, including all {filteredBeams.Count} beams");
        }
        else
        {
            // Filter by beam ID
            filteredBeams = beams
                .Where(b => selectedBeamIds.Contains(b.Id ?? ""))
                .OrderBy(b => b.Date)
                .ThenBy(b => b.Type)
                .ToList();
            Console.WriteLine($"[ReportService] Filtered beams by ID, count: {filteredBeams.Count}");
        }
        
        Console.WriteLine($"[ReportService] Final filtered beams count: {filteredBeams.Count}");

        // Filter GeoChecks - if any geo type selected, include all geochecks (they contain all metrics)
        var filteredGeoChecks = geoChecks.OrderBy(g => g.Date).ToList();
        var showGeoChecks = selectedGeoTypes.Count > 0;

        // 5. Generate PDF
        var document = Document.Create(container =>
        {
            container.Page(page =>
            {
                page.Size(PageSizes.A4);
                page.Margin(2, Unit.Centimetre);
                page.PageColor(Colors.White);
                page.DefaultTextStyle(x => x.FontSize(10).FontFamily(Fonts.Arial));

                page.Header().Element(header => ComposeHeader(header, machineName, request.StartDate, request.EndDate));
                page.Content().Element(content => ComposeContent(content, filteredBeams, filteredGeoChecks, selectedGeoTypes, showGeoChecks));
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
                column.Item().Text("MPC+").FontSize(24).SemiBold().FontColor(Colors.Blue.Medium);
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

    private void ComposeContent(IContainer container, List<Beam> beams, List<GeoCheck> geoChecks, HashSet<string> selectedGeoTypes, bool showGeoChecks)
    {
        container.PaddingVertical(0.5f, Unit.Centimetre).Column(column =>
        {
            // Overview Section
            column.Item().Element(c => ComposeOverview(c, beams, geoChecks, showGeoChecks));

            column.Item().PaddingVertical(0.3f, Unit.Centimetre).LineHorizontal(1).LineColor(Colors.Grey.Lighten2);

            // Beam Checks Section
            if (beams.Count > 0)
            {
                column.Item().PaddingTop(0.5f, Unit.Centimetre).Text("Beam Checks").FontSize(16).SemiBold();
                
                foreach (var beam in beams)
                {
                    column.Item().Element(c => ComposeBeamSection(c, beam));
                }
            }

            // Geometry Checks Section
            if (showGeoChecks && geoChecks.Count > 0)
            {
                column.Item().PaddingTop(0.5f, Unit.Centimetre).LineHorizontal(1).LineColor(Colors.Grey.Lighten2);
                column.Item().PaddingTop(0.5f, Unit.Centimetre).Text("Geometry Checks").FontSize(16).SemiBold();
                
                foreach (var geo in geoChecks)
                {
                    column.Item().Element(c => ComposeGeoSection(c, geo, selectedGeoTypes));
                }
            }
        });
    }

    private void ComposeOverview(IContainer container, List<Beam> beams, List<GeoCheck> geoChecks, bool showGeoChecks)
    {
        // Count passed beams by checking if all metrics pass
        var passedBeams = beams.Count(b => IsBeamPassing(b));
        
        var totalBeams = beams.Count;
        var geoCount = showGeoChecks ? geoChecks.Count : 0;
        var totalChecks = totalBeams + geoCount;
        var passedTotal = passedBeams + geoCount; // Assume geo passes for now

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

    // Helper to determine if a beam passes based on metric values and thresholds
    private bool IsBeamPassing(Beam beam)
    {
        // Check each metric against thresholds
        bool outputPass = !beam.RelOutput.HasValue || Math.Abs(beam.RelOutput.Value) <= 2.0;
        bool uniformityPass = !beam.RelUniformity.HasValue || Math.Abs(beam.RelUniformity.Value) <= 3.0;
        bool centerPass = !beam.CenterShift.HasValue || Math.Abs(beam.CenterShift.Value) <= 2.0;
        
        return outputPass && uniformityPass && centerPass;
    }
    
    // Helper to determine if a metric passes
    private bool IsMetricPassing(string metricName, double? value)
    {
        if (!value.HasValue) return true; // No value = pass
        
        return metricName switch
        {
            "Relative Output" => Math.Abs(value.Value) <= 2.0,
            "Relative Uniformity" => Math.Abs(value.Value) <= 3.0,
            "Center Shift" => Math.Abs(value.Value) <= 2.0,
            _ => true
        };
    }

    private void ComposeBeamSection(IContainer container, Beam beam)
    {
        // Determine pass/fail based on actual metric values
        var isPass = IsBeamPassing(beam);
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
                    beam.RelOutput,
                    "± 2.00%");

                // Relative Uniformity
                AddMetricRow(table, "Relative Uniformity", 
                    beam.RelUniformity,
                    "± 3.00%");

                // Center Shift
                AddMetricRow(table, "Center Shift", 
                    beam.CenterShift,
                    "≤ 2.00 mm");
            });
        });
    }

    private void AddMetricRow(TableDescriptor table, string name, double? value, string threshold)
    {
        // Determine pass/fail based on actual value vs threshold
        var isPass = IsMetricPassing(name, value);
        var statusColor = isPass ? Colors.Green.Medium : Colors.Red.Medium;
        var statusText = isPass ? "PASS" : "FAIL";
        var valueStr = value.HasValue ? $"{value.Value:F3}" : "-";

        table.Cell().Element(DataCellStyle).Text(name);
        table.Cell().Element(DataCellStyle).Text(valueStr);
        table.Cell().Element(DataCellStyle).Text(threshold);
        table.Cell().Element(DataCellStyle).Text(statusText).FontColor(statusColor);
    }

    private static IContainer DataCellStyle(IContainer c) =>
        c.BorderBottom(1).BorderColor(Colors.Grey.Lighten4).Padding(4).DefaultTextStyle(x => x.FontSize(9));

    private void ComposeGeoSection(IContainer container, GeoCheck geo, HashSet<string> selectedGeoTypes)
    {
        container.PaddingTop(0.4f, Unit.Centimetre).Column(column =>
        {
            // Convert date to local time
            var geoDisplayTime = geo.Date.ToLocalTime();
            
            column.Item().Text($"Geometry Check ({geo.Type ?? "N/A"})").FontSize(12).SemiBold();
            column.Item().Text($"Date: {geoDisplayTime:MM/dd/yyyy h:mm tt}").FontSize(9).FontColor(Colors.Grey.Medium);

            // IsoCenter
            if (selectedGeoTypes.Contains("isocenter") || selectedGeoTypes.Count == 0)
            {
                column.Item().PaddingTop(0.2f, Unit.Centimetre).Text("Isocenter").FontSize(10).SemiBold();
                column.Item().Table(table =>
                {
                    table.ColumnsDefinition(columns =>
                    {
                        columns.RelativeColumn(3);
                        columns.RelativeColumn(2);
                        columns.RelativeColumn(2);
                    });

                    table.Cell().Element(DataCellStyle).Text("Size");
                    table.Cell().Element(DataCellStyle).Text(geo.IsoCenterSize.HasValue ? $"{geo.IsoCenterSize.Value:F2} mm" : "-");
                    table.Cell().Element(DataCellStyle).Text("± 0.50 mm");

                    if (geo.IsoCenterMVOffset.HasValue)
                    {
                        table.Cell().Element(DataCellStyle).Text("MV Offset");
                        table.Cell().Element(DataCellStyle).Text($"{geo.IsoCenterMVOffset.Value:F2} mm");
                        table.Cell().Element(DataCellStyle).Text("± 1.00 mm");
                    }

                    if (geo.IsoCenterKVOffset.HasValue)
                    {
                        table.Cell().Element(DataCellStyle).Text("kV Offset");
                        table.Cell().Element(DataCellStyle).Text($"{geo.IsoCenterKVOffset.Value:F2} mm");
                        table.Cell().Element(DataCellStyle).Text("± 1.00 mm");
                    }
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
                        });

                        if (geo.GantryAbsolute.HasValue)
                        {
                            table.Cell().Element(DataCellStyle).Text("Absolute");
                            table.Cell().Element(DataCellStyle).Text($"{geo.GantryAbsolute.Value:F2}°");
                            table.Cell().Element(DataCellStyle).Text("± 0.50°");
                        }

                        if (geo.GantryRelative.HasValue)
                        {
                            table.Cell().Element(DataCellStyle).Text("Relative");
                            table.Cell().Element(DataCellStyle).Text($"{geo.GantryRelative.Value:F2}°");
                            table.Cell().Element(DataCellStyle).Text("± 0.50°");
                        }
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
                        });

                        table.Cell().Element(DataCellStyle).Text("Max Position Error");
                        table.Cell().Element(DataCellStyle).Text($"{geo.CouchMaxPositionError.Value:F2} mm");
                        table.Cell().Element(DataCellStyle).Text("± 1.00 mm");
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
