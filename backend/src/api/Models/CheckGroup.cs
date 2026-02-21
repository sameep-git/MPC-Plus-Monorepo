using Api.Models;

namespace Api.Models;

public record CheckGroup(DateTime Timestamp, List<Beam> Beams);
