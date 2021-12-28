# Motivation
I was sick of how limited VeryFitPro application was so i wrote a program to copy data collected from the smartwatch.
I compared bluethoot log from my rooted phone with logs of the application to understand package structure and data meaning.
I didn't dig into every other aspect other than data logging (heart rate, sleep and activity) because I only needed those, then changed watch. If someone needs to dig deeper this is a good starting point. 

## Requiremets ##
	* python >= 3.7
	* bluepy
	* Wireshark to analyze btsnoop_hci.log
