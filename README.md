# gamut-volume-python

*Gamut volume calculation and visualisation in Python*  

This project is based on Matlab code from IDMS V1.1 Section 5.32,  
which can be obtained at DOI: [10.55410/bjxb8678](https://www.sid.org/Standards/ICDM-DOI#gamut_volume_1.1r02)  

## Pre-requisites

- Python  
- Jupyter  
- numpy  
- matplotlib  
- colour-science  

## Function reference

### cgats

Read from and write to a CGATS data file, the standard ASCII CGATS.17 file format is recommended.  

### make_gamut_envelope

Convert RGB/XYZ data to RGB/3D color space coordinate data.  

- Supported model:  
  - CIELAB-D50: RGB/LAB  
  - CAM16-UCS: RGB/Jab  
  - ICtCp: RGB/ICtCp  

### get_volume

Take the RGB/3D color space coordinate data as input and return the gamut volume in delta E3.  
The [Moller-Trumbore ray-triangle intersection algorithm](https://doi.org/10.1080/10867651.1997.10487472) is used.  
If a reference is provided, calculate the gamut volume coverage.  

### plot_rings

Convert the gamut volume into a 2D gamut ring graph.  
If a reference is provided, both the gamut volume and gamut volume coverage will be shown in the graph title.  
