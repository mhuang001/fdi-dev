# -*- coding: utf-8 -*-
nds2 = \
    """0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 


0 0 0 0 0 
0 0 0 1 0 
5 4 3 2 1 
0 0 0 3 0 


0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 


#=== dimension 4

0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 


0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 


0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 
0 0 0 0 0 


#=== dimension 4

"""

nds3 = \
    """0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 


0 0 5 0 
0 0 4 0 
0 0 3 0 
0 1 2 3 
0 0 1 0 


0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 


#=== dimension 4

0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 


0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 


0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 
0 0 0 0 


#=== dimension 4

"""

out_TableDataset =\
    """# TableDataset
# description = "UNKNOWN"
# meta = MetaData{[], listeners = []}
# data = 

# col1 col2
# eV cnt
1 0 
4.4 43.2 
5400.0 2000.0 

"""

out_CompositeDataset =\
    """# CompositeDataset
# description = "UNKNOWN"
# meta = MetaData{[m1 = NumericParameter{ 2.3 (sec) <float>, "a different param in metadata", dflt None, vld None tcode=None}, ], listeners = []}
# data = 


# [ dataset 1 ]
# ArrayDataset
# description = "arraydset 1"
# meta = MetaData{[], listeners = []}
# unit = "ev"
# data = 

768 
4.4 
5400.0 


# [ dataset 2 ]
# TableDataset
# description = "Example table"
# meta = MetaData{[], listeners = []}
# data = 

# Time Energy
# sec eV
0.0 100.0 
1.0 102.0 
2.0 104.0 
3.0 106.0 
4.0 108.0 

"""
