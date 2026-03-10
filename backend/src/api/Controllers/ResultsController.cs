using Api.Models;
using Api.Repositories.Abstractions;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ResultsController : ControllerBase
{
    private readonly IBeamRepository _beamRepository;
    private readonly IGeoCheckRepository _geoCheckRepository;
    private readonly IThresholdRepository _thresholdRepository;

    public ResultsController(
        IBeamRepository beamRepository, 
        IGeoCheckRepository geoCheckRepository,
        IThresholdRepository thresholdRepository)
    {
        _beamRepository = beamRepository;
        _geoCheckRepository = geoCheckRepository;
        _thresholdRepository = thresholdRepository;
    }

    [HttpGet]
    public async Task<ActionResult<MonthlyResults>> Get(
        [FromQuery] int month,
        [FromQuery] int year,
        [FromQuery] string machineId,
        CancellationToken cancellationToken = default)
    {
        // Validate month range (1-12)
        if (month < 1 || month > 12)
        {
            return BadRequest("Month must be between 1 and 12.");
        }

        // Validate year (reasonable range)
        if (year < 1900 || year > 2100)
        {
            return BadRequest("Year must be between 1900 and 2100.");
        }

        // Validate machineId
        if (string.IsNullOrWhiteSpace(machineId))
        {
            return BadRequest("MachineId is required.");
        }

        // Get all beam checks for this machine, month, and year
        var startDate = new DateTime(year, month, 1);
        var endDate = month == 12 
            ? new DateTime(year + 1, 1, 1).AddDays(-1)
            : new DateTime(year, month + 1, 1).AddDays(-1);
        
        var beamChecks = await _beamRepository.GetAllAsync(
            machineId: machineId,
            startDate: startDate,
            endDate: endDate,
            cancellationToken: cancellationToken);

        var geoChecks = await _geoCheckRepository.GetAllAsync(
            machineId: machineId,
            startDate: startDate,
            endDate: endDate,
            includeDetails: false, // Don't include heavy leaf data for list view
            cancellationToken: cancellationToken);
            
        var thresholds = (await _thresholdRepository.GetAllAsync(cancellationToken)).ToList();

        // Group by date and aggregate status + example display values + approval status + counts
        var dailyChecks = new Dictionary<DateOnly, (string? beamStatus, double? beamValue, bool beamApproved, int beamCount, string? geoStatus, double? geoValue, bool geoApproved, int geoCount)>();
        
        // Process beam checks
        foreach (var check in beamChecks)
        {
            var date = DateOnly.FromDateTime(check.Timestamp);
            var status = DetermineCheckStatus(check, thresholds);
            double? value = check.RelOutput ?? check.RelUniformity ?? check.CenterShift;
            bool isApproved = !string.IsNullOrEmpty(check.ApprovedBy);

            if (dailyChecks.ContainsKey(date))
            {
                var (existingBeamStatus, existingBeamValue, existingBeamApproved, existingBeamCount, geoStatus, geoValue, geoApproved, geoCount) = dailyChecks[date];
                // Aggregate approval: must ALL be approved
                bool newBeamApproved = existingBeamApproved && isApproved;
                dailyChecks[date] = (AggregateStatuses(existingBeamStatus, status), existingBeamValue ?? value, newBeamApproved, existingBeamCount + 1, geoStatus, geoValue, geoApproved, geoCount);
            }
            else
            {
                // Default geoApproved true if no geo checks yet
                dailyChecks[date] = (status, value, isApproved, 1, null, null, true, 0); 
            }
        }

        // Process geometry checks
        foreach (var check in geoChecks)
        {
            var date = DateOnly.FromDateTime(check.Timestamp);
            var status = DetermineGeoCheckStatus(check, thresholds);
            double? value = check.IsoCenterSize ?? check.IsoCenterMVOffset ?? check.GantryAbsolute; // Prioritize IsoCenterSize, then geo-specific metrics as fallbacks
            bool isApproved = !string.IsNullOrEmpty(check.ApprovedBy);

            if (dailyChecks.ContainsKey(date))
            {
                var (beamStatus, beamValue, beamApproved, beamCount, existingGeoStatus, existingGeoValue, existingGeoApproved, existingGeoCount) = dailyChecks[date];
                
                // If existingGeoStatus is null, it means this is the first geo check for this date
                bool newGeoApproved = (existingGeoStatus == null) ? isApproved : (existingGeoApproved && isApproved);
                
                dailyChecks[date] = (beamStatus, beamValue, beamApproved, beamCount, AggregateStatuses(existingGeoStatus, status), existingGeoValue ?? value, newGeoApproved, existingGeoCount + 1);
            }
            else
            {
                // No beam checks for this date, only geo checks
                dailyChecks[date] = (null, null, true, 0, status, value, isApproved, 1); 
            }
        }

        var checks = dailyChecks
            .OrderBy(kvp => kvp.Key)
            .Select(kvp => new DayCheckStatus
            {
                Date = kvp.Key.ToDateTime(TimeOnly.MinValue),
                BeamCheckStatus = kvp.Value.beamStatus,
                GeometryCheckStatus = kvp.Value.geoStatus,
                BeamValue = kvp.Value.beamValue,
                GeometryValue = kvp.Value.geoValue,
                BeamApproved = kvp.Value.beamApproved,
                GeometryApproved = kvp.Value.geoApproved,
                BeamCount = kvp.Value.beamCount,
                GeometryCheckCount = kvp.Value.geoCount
            })
            .ToList();

        var monthlyResults = new MonthlyResults
        {
            Month = month,
            Year = year,
            MachineId = machineId,
            Checks = checks.AsReadOnly()
        };

        return Ok(monthlyResults);
    }

    // Look up a threshold value
    private static double? FindThreshold(IEnumerable<Threshold> thresholds, string machineId, string checkType, string metricType, string? beamVariant = null)
    {
        var match = thresholds.FirstOrDefault(t =>
            t.MachineId == machineId &&
            t.CheckType.Equals(checkType, StringComparison.OrdinalIgnoreCase) &&
            t.MetricType.Equals(metricType, StringComparison.OrdinalIgnoreCase) &&
            (beamVariant == null || string.Equals(t.BeamVariant, beamVariant, StringComparison.OrdinalIgnoreCase)));
        return match?.Value;
    }

    private static bool IsWithinThreshold(double? value, double? threshold)
    {
        if (!value.HasValue || !threshold.HasValue) return true;
        return Math.Abs(value.Value) <= threshold.Value;
    }

    /// <summary>
    /// Determine the status of a single beam check based on thresholds.
    /// </summary>
    private static string DetermineCheckStatus(Beam beam, IReadOnlyList<Threshold> thresholds)
    {
        var outputThreshold = FindThreshold(thresholds, beam.MachineId, "beam", "Relative Output", beam.Type);
        var uniformityThreshold = FindThreshold(thresholds, beam.MachineId, "beam", "Relative Uniformity", beam.Type);
        var centerShiftThreshold = FindThreshold(thresholds, beam.MachineId, "beam", "Center Shift", beam.Type);

        if (!IsWithinThreshold(beam.RelOutput, outputThreshold)) return "fail";
        if (!IsWithinThreshold(beam.RelUniformity, uniformityThreshold)) return "fail";
        if (!IsWithinThreshold(beam.CenterShift, centerShiftThreshold)) return "fail";

        return "pass";
    }

    /// <summary>
    /// Determine the status of a geometry check based on thresholds.
    /// </summary>
    private static string DetermineGeoCheckStatus(GeoCheck geo, IReadOnlyList<Threshold> thresholds)
    {
        var checks = new (string metricType, double? value)[] {
            ("Iso Center Size", geo.IsoCenterSize),
            ("Iso Center MV Offset", geo.IsoCenterMVOffset),
            ("Iso Center KV Offset", geo.IsoCenterKVOffset),
            ("Collimation Rotation Offset", geo.CollimationRotationOffset),
            ("Gantry Absolute", geo.GantryAbsolute),
            ("Gantry Relative", geo.GantryRelative),
            ("Couch Lat", geo.CouchLat),
            ("Couch Lng", geo.CouchLng),
            ("Couch Vrt", geo.CouchVrt),
            ("Max Position Error", geo.CouchMaxPositionError),
            ("Mean Offset A", geo.MeanOffsetA),
            ("Max Offset A", geo.MaxOffsetA),
            ("Mean Offset B", geo.MeanOffsetB),
            ("Max Offset B", geo.MaxOffsetB),
            ("Jaw X1", geo.JawX1),
            ("Jaw X2", geo.JawX2),
            ("Jaw Y1", geo.JawY1),
            ("Jaw Y2", geo.JawY2),
            ("Parallelism X1", geo.JawParallelismX1),
            ("Parallelism X2", geo.JawParallelismX2),
            ("Parallelism Y1", geo.JawParallelismY1),
            ("Parallelism Y2", geo.JawParallelismY2)
        };

        foreach (var check in checks)
        {
            var threshold = FindThreshold(thresholds, geo.MachineId, "geometry", check.metricType);
            if (!IsWithinThreshold(check.value, threshold)) return "fail";
        }

        var leafThreshold = FindThreshold(thresholds, geo.MachineId, "geometry", "mlc_leaf_position");
        if (leafThreshold.HasValue)
        {
            if (geo.MLCLeavesA != null && geo.MLCLeavesA.Values.Any(v => !IsWithinThreshold(v, leafThreshold))) return "fail";
            if (geo.MLCLeavesB != null && geo.MLCLeavesB.Values.Any(v => !IsWithinThreshold(v, leafThreshold))) return "fail";
        }

        var backlashThreshold = FindThreshold(thresholds, geo.MachineId, "geometry", "mlc_backlash");
        if (backlashThreshold.HasValue)
        {
            if (geo.MLCBacklashA != null && geo.MLCBacklashA.Values.Any(v => !IsWithinThreshold(v, backlashThreshold))) return "fail";
            if (geo.MLCBacklashB != null && geo.MLCBacklashB.Values.Any(v => !IsWithinThreshold(v, backlashThreshold))) return "fail";
        }

        return "pass";
    }

    /// <summary>
    /// Aggregate two statuses, returning the worse one.
    /// Hierarchy: fail > warning > pass
    /// </summary>
    private static string AggregateStatuses(string? status1, string? status2)
    {
        if (status1 == "fail" || status2 == "fail") return "fail";
        if (status1 == "warning" || status2 == "warning") return "warning";
        return status2 ?? status1 ?? "pass";
    }
}