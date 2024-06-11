# gamut-volume-python
CIELab gamut volume calculation and visualisation in Python  
This project is based on Matlab code from IDMS V1.1 Section 5.32, which can be obtained at DOI: [10.55410/bjxb8678](https://www.sid.org/Standards/ICDM-DOI#gamut_volume_1.1r02)  
## Pre-requisites
- Python  
- Jupyter  
- numpy  
- matplotlib  
- (optional) colour-science  
## Function reference
### cgats
Read from and write in a CGATS data file, the standard ASCII CGATS.17 file format is recommended.  
### make_gamut_envelope
Read RGB/XYZ data from CGATS file, and translate to RGB/LAB data.  
In the current version, the Bradford transform matrix is ​​used directly to achieve chromatic adaptation.  
If higher accuracy is required, it is recommended to use the chromatic adaptation fucntion from colour-science.  
### make_tesselation
Construct a reference RGB tesselation from a unique set of the given greyscale values.   
### get_volume
Take the RGB/LAB data as input and return the CIELAB gamut volume in delta E3.  
The [Moller-Trumbore ray-triangle intersection algorithm](https://doi.org/10.1080/10867651.1997.10487472) is used.  