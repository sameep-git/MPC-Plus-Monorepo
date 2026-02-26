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

    public ResultsController(
        IBeamRepository beamRepository, 
        IGeoCheckRepository geoCheckRepository)
    {
        _beamRepository = beamRepository;
        _geoCheckRepository = geoCheckRepository;
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
            
        // Group by date and aggregate status + example display values + approval status + counts
        var dailyChecks = new Dictionary<DateOnly, (string? beamStatus, double? beamValue, bool beamApproved, int beamCount, string? geoStatus, double? geoValue, bool geoApproved, int geoCount)>();
        
        // Process beam checks
        foreach (var check in beamChecks)
        {
            var date = DateOnly.FromDateTime(check.Timestamp);
            var status = DetermineCheckStatus(check);
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
            var status = DetermineGeoCheckStatus(check);
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

    /// <summary>
    /// Determine the status of a single beam check based on pass criteria.
    /// </summary>
    private static string DetermineCheckStatus(Beam beam)
    {
        // Placeholder until threshold logic is reworked
        return "pass";
    }

    /// <summary>
    /// Determine the status of a geometry check based on pass criteria.
    /// </summary>
    private static string DetermineGeoCheckStatus(GeoCheck geoCheck)
    {
        // Placeholder until threshold logic is reworked
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