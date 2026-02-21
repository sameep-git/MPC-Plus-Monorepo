# MPC Data Manipulation

This section of the software is designed to monitor the iDrive for new data and recieve data from user inputs. 


# Happy Path
1. The data's path information is passed to DataProcessor.py
2. DataProcessor.py is create the model of the given beam and passes the model to Extractor.py and Uploader.py
		2.1. Extractor.py reads the Results.csv file of the beam and 				   	sets the corrosponding vairables to the values given in the csv fiie.
		2.2. Uploader.py established a connection with the Supabase database. It uploads the beam's data to the corrosponding table in the database. 
	


# File Structue

All files needed for the data manipulation of the MPC data are stored in the data_manipulation directory.
This directory has 3 sub-directories
 1. file_monitoring
 2. ELT
 3. models

**file_monitoring**
This holds the system that moniors the iDrive. Once new data has been added to the iDrive, file_monitor.py will call DataProcessor.py will the path of the new data.
**ELT**
This folder holds the system that extracts data from the csv file and uploads them to the database.
**models**
The folder holds models for beams with the 'x' and 'e' suffux and the Geometry Check (6x) beam. Each model contains a getter and setter for beam type, date, and all vairables in the csv file. 
