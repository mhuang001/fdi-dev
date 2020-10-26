# -*- coding: utf-8 -*-
nds20 = \
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

nds30 = \
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

nds2 =\
    """0  0  0  0  0
0  0  0  0  0
0  0  0  0  0
0  0  0  0  0


0  0  0  0  0
0  0  0  1  0
5  4  3  2  1
0  0  0  3  0


0  0  0  0  0
0  0  0  0  0
0  0  0  0  0
0  0  0  0  0


#=== dimension 4

0  0  0  0  0
0  0  0  0  0
0  0  0  0  0
0  0  0  0  0


0  0  0  0  0
0  0  0  0  0
0  0  0  0  0
0  0  0  0  0


0  0  0  0  0
0  0  0  0  0
0  0  0  0  0
0  0  0  0  0


#=== dimension 4

"""

nds3 =\
    """0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0


0  0  5  0
0  0  4  0
0  0  3  0
0  1  2  3
0  0  1  0


0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0


#=== dimension 4

0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0


0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0


0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0
0  0  0  0


#=== dimension 4

"""

out_GenericDataset =\
    """# GenericDataset
description= {'test GD'},
meta= {
    a= {NumericParameter{ 3.4 (None) <float>, "num par", default= 2.0, valid= [[[0, 30], 'nok']] tcode=None}},
    b= {DateParameter{ "FineTime{2019-02-19T01:02:03.456789 TAI(1929229323456789) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}", "date par", default= FineTime{1958-01-01T00:00:00.99 TAI(99) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}, valid= [[[0, 9999999999], 'dok']] tcode=%Y-%m-%dT%H:%M:%S.%f UTC}},
    c= {StringParameter{ "Right", "str par", default= cliche, valid= [['', 'sok']] tcode=B}}}
data =

88.8
# GenericDataset
description= {'test GD'},
meta= {a= 3.4, b= 2019-02-19T01:02:03.456789 TA...3456789), c= 'Right'}
data =

88.8
# GenericDataset
description, meta
data =

88.8
"""

out_TableDataset0 =\
    """# TableDataset
description= {'UNKNOWN'},
meta= {
    a= {NumericParameter{ 3.4 (None) <float>, "num par", default= 2.0, valid= [[[0, 30], 'nok']] tcode=None}},
    b= {DateParameter{ "FineTime{2019-02-19T01:02:03.456789 TAI(1929229323456789) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}", "date par", default= FineTime{1958-01-01T00:00:00.99 TAI(99) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}, valid= [[[0, 9999999999], 'dok']] tcode=%Y-%m-%dT%H:%M:%S.%f UTC}},
    c= {StringParameter{ "Right", "str par", default= cliche, valid= [['', 'sok']] tcode=B}}}
data =

# col1 col2
# eV cnt
1 0 
4.4 43.2 
5400.0 2000.0 

"""

out_TableDataset =\
    """# TableDataset
description= {'UNKNOWN'},
meta= {
    a= {NumericParameter{ 3.4 (None) <float>, "num par", default= 2.0, valid= [[[0, 30], 'nok']] tcode=None}},
    b= {DateParameter{ "FineTime{2019-02-19T01:02:03.456789 TAI(1929229323456789) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}", "date par", default= FineTime{1958-01-01T00:00:00.99 TAI(99) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}, valid= [[[0, 9999999999], 'dok']] tcode=%Y-%m-%dT%H:%M:%S.%f UTC}},
    c= {StringParameter{ "Right", "str par", default= cliche, valid= [['', 'sok']] tcode=B}}}
data =

======  =======
  col1     col2
  (eV)    (cnt)
======  =======
   1        0
   4.4     43.2
5400     2000
======  =======


"""

out_CompositeDataset0 =\
    """# CompositeDataset
description= {'test CD'},
meta= {
    a= {NumericParameter{ 3.4 (None) <float>, "num par", default= 2.0, valid= [[[0, 30], 'nok']] tcode=None}},
    b= {DateParameter{ "FineTime{2019-02-19T01:02:03.456789 TAI(1929229323456789) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}", "date par", default= FineTime{1958-01-01T00:00:00.99 TAI(99) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}, valid= [[[0, 9999999999], 'dok']] tcode=%Y-%m-%dT%H:%M:%S.%f UTC}},
    c= {StringParameter{ "Right", "str par", default= cliche, valid= [['', 'sok']] tcode=B}},
    m1= {NumericParameter{ 2.3 (sec) <float>, "a different param in metadata", default= None, valid= None tcode=None}}}data =


# [ dataset 1 ]
# ArrayDataset
description= {'arraydset 1'},
meta= {},
type= {None},
default= {None},
typecode= {None},
unit= {'ev'}
data =

768 
4.4 
5400.0 


# [ dataset 2 ]
# TableDataset
description= {'Example table'}, meta= {}
data =

# Time Energy
# sec eV
0.0 100.0 
1.0 102.0 
2.0 104.0 
3.0 106.0 
4.0 108.0 

"""

out_CompositeDataset =\
    """# CompositeDataset
description= {'test CD'},
meta= {
    a= {NumericParameter{ 3.4 (None) <float>, "num par", default= 2.0, valid= [[[0, 30], 'nok']] tcode=None}},
    b= {DateParameter{ "FineTime{2019-02-19T01:02:03.456789 TAI(1929229323456789) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}", "date par", default= FineTime{1958-01-01T00:00:00.99 TAI(99) fmt=%Y-%m-%dT%H:%M:%S.%f UTC}, valid= [[[0, 9999999999], 'dok']] tcode=%Y-%m-%dT%H:%M:%S.%f UTC}},
    c= {StringParameter{ "Right", "str par", default= cliche, valid= [['', 'sok']] tcode=B}},
    m1= {NumericParameter{ 2.3 (sec) <float>, "a different param in metadata", default= None, valid= None tcode=None}}}data =


#     [ dataset 1 ]
# ArrayDataset
description= {'arraydset 1'},
meta= {},
type= {None},
default= {None},
typecode= {None},
unit= {'ev'}
data =

768  4.4  5400

#     [ dataset 2 ]
# TableDataset
description= {'Example table'}, meta= {}
data =

=======  ========
   Time    Energy
  (sec)      (eV)
=======  ========
      0       100
      1       102
      2       104
      3       106
      4       108
=======  ========


"""
