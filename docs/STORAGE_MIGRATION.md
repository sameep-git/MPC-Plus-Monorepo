# Image Storage Configuration Guide

This document describes how beam check images are served and what to change when switching between storage providers.

## Architecture

```
Frontend (getImageUrl)
       │
       ├── NEXT_PUBLIC_STORAGE_URL set?
       │       YES → Direct to storage (MinIO or Supabase public bucket)
       │       NO  → Backend proxy at GET /api/image?path=<path>
       │                    │
       │                    ├── Backend env = "minio"  → MinIO SDK
       │                    └── Backend env = "supabase" → Supabase Storage API
```

## Frontend Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API base URL (e.g. `http://localhost:5132/api`) |
| `NEXT_PUBLIC_STORAGE_URL` | No | Direct storage base URL. If set, images bypass the backend. |

### Mode 1: Backend Proxy (Default, Recommended)

Leave `NEXT_PUBLIC_STORAGE_URL` **unset**. Images go through `GET /api/image?path=<path>`.

```env
NEXT_PUBLIC_API_URL=http://localhost:5132/api
# NEXT_PUBLIC_STORAGE_URL=   ← not set
```

### Mode 2: Direct Storage Access

Set `NEXT_PUBLIC_STORAGE_URL` to the storage base URL. The image path from `beam.imagePaths` is appended directly.

```env
# MinIO (local dev)
NEXT_PUBLIC_STORAGE_URL=http://localhost:9000/beam-images

# Supabase Storage (prod)
NEXT_PUBLIC_STORAGE_URL=https://<project>.supabase.co/storage/v1/object/public/beam-images
```

---

## Backend Changes for MinIO ↔ Supabase Migration

The backend `/api/image` endpoint needs an `IImageStorageService` with two implementations.

### Environment Variables (Backend — C# appsettings)

```json
// appsettings.Development.json (MinIO)
{
  "Storage": {
    "Provider": "minio",
    "MinIO": {
      "Endpoint": "localhost:9000",
      "AccessKey": "minioadmin",
      "SecretKey": "minioadmin",
      "Bucket": "beam-images",
      "UseSSL": false
    }
  }
}
```

```json
// appsettings.Production.json (Supabase)
{
  "Storage": {
    "Provider": "supabase",
    "Supabase": {
      "Url": "https://<project>.supabase.co",
      "ServiceKey": "<supabase-service-role-key>",
      "Bucket": "beam-images"
    }
  }
}
```

### Service Registration

```csharp
var provider = builder.Configuration["Storage:Provider"];
if (provider == "minio")
    builder.Services.AddSingleton<IImageStorageService, MinioImageStorageService>();
else
    builder.Services.AddSingleton<IImageStorageService, SupabaseImageStorageService>();
```

### MinIO Implementation (NuGet: `Minio`)

```csharp
public class MinioImageStorageService : IImageStorageService
{
    private readonly IMinioClient _client;
    private readonly string _bucket;

    public async Task<Stream> GetImageAsync(string path)
    {
        var ms = new MemoryStream();
        await _client.GetObjectAsync(new GetObjectArgs()
            .WithBucket(_bucket)
            .WithObject(path)
            .WithCallbackStream(stream => stream.CopyTo(ms)));
        ms.Position = 0;
        return ms;
    }
}
```

### Supabase Implementation

```csharp
public class SupabaseImageStorageService : IImageStorageService
{
    private readonly HttpClient _http;
    private readonly string _baseUrl;
    private readonly string _bucket;

    public async Task<Stream> GetImageAsync(string path)
    {
        var url = $"{_baseUrl}/storage/v1/object/{_bucket}/{path}";
        return await _http.GetStreamAsync(url);
    }
}
```

---

## Migration Checklist: Supabase → MinIO

### Backend
- [ ] Install `Minio` NuGet package
- [ ] Create `MinioImageStorageService` implementing `IImageStorageService`
- [ ] Add MinIO config to `appsettings.Development.json`
- [ ] Set `Storage:Provider=minio` in dev environment
- [ ] Ensure MinIO is running (e.g. `docker run -p 9000:9000 minio/minio server /data`)
- [ ] Create the bucket and upload test images

### Frontend
- [ ] No code changes needed
- [ ] Optionally set `NEXT_PUBLIC_STORAGE_URL=http://localhost:9000/beam-images` for direct access

## Migration Checklist: MinIO → Supabase

### Backend
- [ ] Create `SupabaseImageStorageService` implementing `IImageStorageService`
- [ ] Add Supabase config to `appsettings.Production.json`
- [ ] Set `Storage:Provider=supabase` in prod environment
- [ ] Create Supabase Storage bucket and set access policy (public or authenticated)

### Frontend
- [ ] No code changes needed
- [ ] If using direct access: update `NEXT_PUBLIC_STORAGE_URL` to Supabase URL
