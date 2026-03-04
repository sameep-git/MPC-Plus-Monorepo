// See https://aka.ms/new-console-template for more information
using System;
using Dapper;

class Program
{
	static void Main(string[] args)
	{
		var hash = "$2a$06$khGWv71gLuAzvOxkrIJbkurI39uhRObk3mRGX0acKtWnf5XNNgKgm";
		var password = "admin123";
		Console.WriteLine("hash: " + hash);
		Console.WriteLine("verify result: " + BCrypt.Net.BCrypt.Verify(password, hash));
		// now try fetching from database using Npgsql + Dapper
		try
		{
			using var conn = new Npgsql.NpgsqlConnection("Host=localhost;Port=5432;Database=mpc_plus;Username=postgres;Password=your_password_here");
			conn.Open();
			var user = conn.QueryFirstOrDefault<dynamic>("select username, password_hash from users where username='admin'");
			Console.WriteLine("db retrieved: " + user?.password_hash);
			Console.WriteLine("db verify: " + BCrypt.Net.BCrypt.Verify(password, (string)user.password_hash));
		}
		catch (Exception ex)
		{
			Console.WriteLine("DB error: " + ex.Message);
		}
	}
}
