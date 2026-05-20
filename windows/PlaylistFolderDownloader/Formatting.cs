namespace PlaylistFolderDownloader;

public static class Formatting
{
    public static string FormatDuration(int? seconds)
    {
        if (seconds is null)
        {
            return "";
        }

        var value = Math.Max(0, seconds.Value);
        var hours = value / 3600;
        var minutes = value % 3600 / 60;
        var secs = value % 60;
        return hours > 0 ? $"{hours}:{minutes:00}:{secs:00}" : $"{minutes}:{secs:00}";
    }

    public static string FormatMediaLabel(MediaFormat format)
    {
        var parts = new[]
        {
            format.Resolution,
            format.Language,
            format.Vcodec is not null and not "none" ? format.Vcodec : null,
            format.Acodec is not null and not "none" ? format.Acodec : null,
            format.Abr is not null ? $"{(int)format.Abr.Value}kbps" : null,
            format.Ext,
            format.FormatId,
        };
        return string.Join(" | ", parts.Where(part => !string.IsNullOrWhiteSpace(part)));
    }
}
