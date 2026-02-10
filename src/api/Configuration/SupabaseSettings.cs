namespace Api.Configuration;

public class SupabaseSettings
{
    public const string SectionName = "Supabase";

    public string? Url { get; init; }

    public string? Key { get; init; }

    /// <summary>
    /// Override PostgREST URL format. Default is "{0}/rest/v1" (Supabase Cloud).
    /// Set to "{0}" for standalone PostgREST which serves at root.
    /// </summary>
    public string RestUrlFormat { get; init; } = "{0}/rest/v1";
}

