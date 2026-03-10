// See https://aka.ms/new-console-template for more information
using System;
using Dapper;

class Program
{
	static void Main(string[] args)
	{
#if DEBUG
		RunDebugPasswordVerification();
#else
		Console.WriteLine("This utility is intended for debug builds only.");
#endif
	}

	private static void RunDebugPasswordVerification()
	{
		var hash = Environment.GetEnvironmentVariable("BCRYPT_TEST_HASH");
		var password = Environment.GetEnvironmentVariable("BCRYPT_TEST_PASSWORD");

		if (string.IsNullOrEmpty(hash) || string.IsNullOrEmpty(password))
		{
			Console.WriteLine("Please set BCRYPT_TEST_HASH and BCRYPT_TEST_PASSWORD environment variables before running this debug utility.");
			return;
		}

		Console.WriteLine("hash: " + hash);
		Console.WriteLine("verify result: " + BCrypt.Net.BCrypt.Verify(password, hash));

		// now try fetching from database using Npgsql + Dapper
		var connectionString = Environment.GetEnvironmentVariable("BCRYPT_TEST_CONNECTION_STRING");
		if (string.IsNullOrEmpty(connectionString))
		{
			Console.WriteLine("Environment variable BCRYPT_TEST_CONNECTION_STRING is not set; skipping database verification.");
			return;
		}

		try
		{
			using var conn = new Npgsql.NpgsqlConnection(connectionString);
			conn.Open();
			var user = conn.QueryFirstOrDefault<dynamic>("select username, password_hash from users where username='admin'");
			Console.WriteLine("db retrieved: " + user?.password_hash);
			if (user?.password_hash != null)
			{
				Console.WriteLine("db verify: " + BCrypt.Net.BCrypt.Verify(password, (string)user.password_hash));
			}
			else
			{
				Console.WriteLine("No user or password_hash returned from database.");
			}
		}
		catch (Exception ex)
		{
			Console.WriteLine("DB error: " + ex.Message);
		}
	}
}
