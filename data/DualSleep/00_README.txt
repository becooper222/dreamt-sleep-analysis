
This README file was generated on [2024-05-31] (YYYY-MM-DD) by [Aleksej Logacjov].
Last updated: [2024-06-05].


-------------------
GENERAL INFORMATION
-------------------
// Title of Dataset: DualSleep
// DOI: https://doi.org/10.18710/UGNIFE
// Contact Information
     // Name: Aleksej Logacjov
     // Institution: Norwegian University of Science and Technology, Department of Computer Science
     // Email: aleksej.logacjov@ntnu.no
     // ORCID: 0000-0002-8834-1744

     // Name: Eivind Schjelderup Skarpsno
     // Institution: Norwegian University of Science and Technology, Department of Computer Science
     // Email: eivind.s.skarpsno@ntnu.no
     // ORCID: 0000-0002-4135-0408

     // Name: Atle Kongsvold
     // Institution: Norwegian University of Science and Technology, Department of Computer Science
     // Email: atle.a.kongsvold@ntnu.no
     // ORCID: 0000-0003-4887-8288

     // Name: Kerstin Bach
     // Institution: Norwegian University of Science and Technology, Department of Computer Science
     // Email: kerstin.bach@ntnu.no
     // ORCID: 0000-0002-4256-7676

     // Name: Paul Jarle Mork
     // Institution: Norwegian University of Science and Technology, Department of Public Health and Nursing
     // Email: paul.mork@ntnu.no
     // ORCID: 0000-0003-3355-2680

// Contributors: See metadata field Contributor.
// Data Type: Sensor data as .csv files.
// Date of data collection/generation: See metadata field Date of Collection.
// Geographic location: See metadata section Geographic Coverage.
// Funding sources: See metadata section Grant Information.

// Description of dataset:
The DualSleep dataset contains acceleration and temperature overnight recordings of 29 participants wearing two accelerometers at the thigh and lower back, together with the corresponding sleep stages/annotations (Wake, Non-REM1, Non-REM2, Non-REM3, REM, Movement). The annotation were created using simultaneous Polysomnography recordings. The study protocol was approved by the Regional Committee for Medical and Health research ethics (reference no. 2015/1748/REK midt) and all participants signed a written informed consent before being enrolled in the study. The DualSleep dataset was used for machine learning experiments in our published paper: "A machine learning model for predicting sleep and wakefulness based on accelerometry, skin temperature and contextual information" (https://doi.org/10.2147/NSS.S452799)

--------------------------
METHODOLOGICAL INFORMATION
--------------------------
// Description of sources and methods used for collection/generation of data:
The study included 29 participants (11 male, 17 female) with mean (SD) age of 40.2 (15) years (range 17-70 years). Eleven of these were referred to the sleep clinic at St. Olavs University Hospital, Trondheim, Norway by their general practitioner/medical specialist to undergo a diagnostic evaluation for a possible sleep disorder (i.e., obstructive sleep apnea, hypersomnia, or insomnia). The remaining 18 participants were recruited among academic staff/researchers by word of mouth. The study protocol was approved by the Regional Committee for Medical and Health research ethics (reference no. 2015/1748/REK midt) and all participants signed a written informed consent before being enrolled in the study.  
All overnight PSG and accelerometer recordings were performed in a sleep laboratory for the 18 participants without known sleep disorders, whereas the eleven participants with a possible sleep disorder underwent an at-home test. The participants were allowed to sleep based on their habitual sleep time and could use an alarm clock if desired. At arrival in the laboratory or at the clinic, the participants were informed about the study protocol. After signing the written informed consent, the participants were equipped with the PSG sensors, including electroencephalography (EEG), right and left electrooculography (EOG), surface electromyography (EMG) on tibialis anterior, electrocardiography (ECG), airflow (thermistor flow sensor and thoracic- and abdominal strain sensor), body position sensor, and oxygen saturation (oximeter attached to the finger), as well as the two three-axial AX3 accelerometers (Axivity Ltd., Newcastle, UK). The accelerometers were attached to the skin at the participants lower back, approximately at the third lumbar vertebra, and the upper right thigh, approximately 10 cm above the upper border of the patella. To attach the accelerometer, a 5x7 cm moisture permeable film (Opsite Flexifix; Smith & Nephew, Watford, UK) was attached to the skin. The accelerometer was then positioned on top of the film using double-sided tape and covered with a second film layer of 10x8 cm. Body accelerations were recorded with a sampling rate of 100 Hz and later downsampled to 50 Hz using the Fourier method. The accelerometer and PSG data were synchronized by aligning the PSG movement sensor signal and the accelerometer signals. The PSG recordings were visually scored in 30 s epochs by trained personnel following the AASM Manual for the Scoring of Sleep and Associated Events.

// Methods for processing the data:
The recordings are given in 50Hz. The temperature signals were upsampled from 1.2Hz to 50Hz and the accelerometer signals were downsampled from 100Hz to 50Hz. The data is provided for each subject as a separate file. Since the files are .csv files, they can easily be read using data analysis tools.

// Facility-, instrument- or software-specific information needed to interpret the data:
The data can be read using any data analysis tool that can read .csv files.


--------------------
DATA & FILE OVERVIEW
--------------------
// File List:
Each subject is stored as a separate file with the subject ID being the filename. Each file contains the following columns: 
- timestamp: Timestamp of the recorded sample in the format
- back_x: Acceleration in x-direction at the lower back in the unit g
- back_y: Acceleration in y-direction at the lower back in the unit g
- back_z: Acceleration in z-direction at the lower back in the unit g
- thigh_x: Acceleration in x-direction at the thigh in the unit g
- thigh_y: Acceleration in y-direction at the thigh in the unit g
- thigh_z: Acceleration in z-direction at the thigh in the unit g
- back_temp: Temperature at the lower back in the unit Celsius
- thigh_temp: Temperature at the thigh in the unit Celsius
- label: Sleep stage annotation as integer code

The labels are coded as follows:
- Wake: 81
- Non-REM1: 82
- Non-REM2: 83
- Non-REM3: 84
- REM: 85
- Movement: 86



--------------------------
SHARING/ACCESS INFORMATION
--------------------------
// Licenses/Restrictions: See Terms tab.
// Links to publications that cite or use the data: See metadata field Related Publication.
// Links/relationships to related data sets: See metadata field Related Datasets.
// Data sources: See metadata field Data Sources.
// Recommended citation: See citation generated by repository.
