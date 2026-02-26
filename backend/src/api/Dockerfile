# Use .NET 9 SDK image for building (matches api.csproj TargetFramework)
FROM mcr.microsoft.com/dotnet/sdk:9.0-alpine AS build
WORKDIR /src

# Copy the csproj and restore dependencies
COPY ["api.csproj", "./"]
RUN dotnet restore "api.csproj"

# Copy the rest of the source code and build
COPY . .
RUN dotnet build "api.csproj" -c Release -o /app/build

# Publish the application
FROM build AS publish
RUN dotnet publish "api.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Use the lighter ASP.NET runtime for the final image
FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS final
WORKDIR /app

# Expose port (8080 is default for .NET containers)
EXPOSE 8080

# Install ICU packages for timezone data compatibility
RUN apk add --no-cache icu-libs tzdata
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false

# Copy files from publish layer
COPY --from=publish /app/publish .

# Determine where images are stored via volume mounting
RUN mkdir -p /app/wwwroot/images

# Start the application
ENTRYPOINT ["dotnet", "api.dll"]
