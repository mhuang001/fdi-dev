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

out_GenericDataset = """level 0
# GenericDataset
description= {'test GD'},
meta= {
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| name   | value             | unit   | type     | valid                     | default         | code   | description     |
+========+===================+========+==========+===========================+=================+========+=================+
| a      | 3.4               | None   | float    | (0, 31): valid            | 2.0             | None   | rule name, if i |
|        |                   |        |          | 99:                       |                 |        | s "valid", "",  |
|        |                   |        |          |                           |                 |        | or "default", i |
|        |                   |        |          |                           |                 |        | s ommited in va |
|        |                   |        |          |                           |                 |        | lue string.     |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| b      | xy (2019-02-19    |        | finetime | (0, 9876543210123456): xy | 1958-01-01      |        | date param      |
|        | 01:02:03.456789   |        |          |                           | 00:00:00.000099 |        |                 |
|        | 1929229323456789) |        |          |                           | 99              |        |                 |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| c      | Invalid (IJK)     |        | string   | '': empty                 | cliche          | B      | str parameter.  |
|        |                   |        |          |                           |                 |        | but only "" is  |
|        |                   |        |          |                           |                 |        | allowed.        |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| d      | off (0b00)        | None   | binary   | 11000 0b01: on            | 0b0             | None   | valid rules des |
|        |                   |        |          | 11000 0b00: off           |                 |        | cribed with bin |
|        |                   |        |          |                           |                 |        | ary masks       |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
MetaData-listeners = ListnerSet{}}
GenericDataset-dataset =
88.8
level 1, repr
# GenericDataset
description= {'test GD'},
meta= {
-------------  -----------------  ----------------
a= 3.4         b= xy (2019-02-19  c= Invalid (IJK)
               01:02:03.456789
               1929229323456789)
d= off (0b00)
-------------  -----------------  ----------------
MetaData-listeners = ListnerSet{}
}
GenericDataset-dataset =
88.8
level 2,
GenericDataset{ 88.8, description = "test GD", meta = a, b, c, d, listeners = ListnerSet{} }"""
out_ArrayDataset = """level 0
# ArrayDataset
description= {'toString tester AD'},
meta= {
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| name   | value             | unit   | type     | valid                     | default         | code   | description     |
+========+===================+========+==========+===========================+=================+========+=================+
| a      | 3.4               | None   | float    | (0, 31): valid            | 2.0             | None   | rule name, if i |
|        |                   |        |          | 99:                       |                 |        | s "valid", "",  |
|        |                   |        |          |                           |                 |        | or "default", i |
|        |                   |        |          |                           |                 |        | s ommited in va |
|        |                   |        |          |                           |                 |        | lue string.     |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| b      | xy (2019-02-19    |        | finetime | (0, 9876543210123456): xy | 1958-01-01      |        | date param      |
|        | 01:02:03.456789   |        |          |                           | 00:00:00.000099 |        |                 |
|        | 1929229323456789) |        |          |                           | 99              |        |                 |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| c      | Invalid (IJK)     |        | string   | '': empty                 | cliche          | B      | str parameter.  |
|        |                   |        |          |                           |                 |        | but only "" is  |
|        |                   |        |          |                           |                 |        | allowed.        |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| d      | off (0b00)        | None   | binary   | 11000 0b01: on            | 0b0             | None   | valid rules des |
|        |                   |        |          | 11000 0b00: off           |                 |        | cribed with bin |
|        |                   |        |          |                           |                 |        | ary masks       |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
MetaData-listeners = ListnerSet{}},
type= {None},
default= {None},
typecode= {None},
unit= {'lyr'}
ArrayDataset-dataset =
0  0  0  0  0
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


level 1, repr
# ArrayDataset
description= {'toString tester AD'},
meta= {
-------------  -----------------  ----------------
a= 3.4         b= xy (2019-02-19  c= Invalid (IJK)
               01:02:03.456789
               1929229323456789)
d= off (0b00)
-------------  -----------------  ----------------
MetaData-listeners = ListnerSet{}
},
type= {None},
default= {None},
typecode= {None},
unit= {'lyr'}
ArrayDataset-dataset =
0  0  0  0  0
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


level 2,
ArrayDataset{ [[[[0, 0, 0, ...0]]], [[[0, 0, 0, ...0]]]] (lyr) <None>, "toString tester AD", default None, tcode=None, meta=
-------------  -----------------  ----------------
a= 3.4         b= xy (2019-02-19  c= Invalid (IJK)
               01:02:03.456789
               1929229323456789)
d= off (0b00)
-------------  -----------------  ----------------
MetaData-listeners = ListnerSet{}}"""
out_TableDataset = """level 0
# TableDataset
description= {'UNKNOWN'},
meta= {
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| name   | value             | unit   | type     | valid                     | default         | code   | description     |
+========+===================+========+==========+===========================+=================+========+=================+
| a      | 3.4               | None   | float    | (0, 31): valid            | 2.0             | None   | rule name, if i |
|        |                   |        |          | 99:                       |                 |        | s "valid", "",  |
|        |                   |        |          |                           |                 |        | or "default", i |
|        |                   |        |          |                           |                 |        | s ommited in va |
|        |                   |        |          |                           |                 |        | lue string.     |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| b      | xy (2019-02-19    |        | finetime | (0, 9876543210123456): xy | 1958-01-01      |        | date param      |
|        | 01:02:03.456789   |        |          |                           | 00:00:00.000099 |        |                 |
|        | 1929229323456789) |        |          |                           | 99              |        |                 |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| c      | Invalid (IJK)     |        | string   | '': empty                 | cliche          | B      | str parameter.  |
|        |                   |        |          |                           |                 |        | but only "" is  |
|        |                   |        |          |                           |                 |        | allowed.        |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| d      | off (0b00)        | None   | binary   | 11000 0b01: on            | 0b0             | None   | valid rules des |
|        |                   |        |          | 11000 0b00: off           |                 |        | cribed with bin |
|        |                   |        |          |                           |                 |        | ary masks       |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
MetaData-listeners = ListnerSet{}}
TableDataset-dataset =
  col1     col2
  (eV)    (cnt)
------  -------
   1        0
   4.4     43.2
5400     2000


level 1, repr
# TableDataset
description= {'UNKNOWN'},
meta= {
-------------  -----------------  ----------------
a= 3.4         b= xy (2019-02-19  c= Invalid (IJK)
               01:02:03.456789
               1929229323456789)
d= off (0b00)
-------------  -----------------  ----------------
MetaData-listeners = ListnerSet{}
}
TableDataset-dataset =
  col1     col2
  (eV)    (cnt)
------  -------
   1        0
   4.4     43.2
5400     2000


level 2,
# TableDataset
description, meta
TableDataset-dataset =
  col1     col2
  (eV)    (cnt)
------  -------
   1        0
   4.4     43.2

(Only display 2 rows of 3 for level=2.)
"""
out_CompositeDataset = """level 0
# CompositeDataset
description= {'test CD'},
meta= {
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| name   | value             | unit   | type     | valid                     | default         | code   | description     |
+========+===================+========+==========+===========================+=================+========+=================+
| a      | 3.4               | None   | float    | (0, 31): valid            | 2.0             | None   | rule name, if i |
|        |                   |        |          | 99:                       |                 |        | s "valid", "",  |
|        |                   |        |          |                           |                 |        | or "default", i |
|        |                   |        |          |                           |                 |        | s ommited in va |
|        |                   |        |          |                           |                 |        | lue string.     |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| b      | xy (2019-02-19    |        | finetime | (0, 9876543210123456): xy | 1958-01-01      |        | date param      |
|        | 01:02:03.456789   |        |          |                           | 00:00:00.000099 |        |                 |
|        | 1929229323456789) |        |          |                           | 99              |        |                 |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| c      | Invalid (IJK)     |        | string   | '': empty                 | cliche          | B      | str parameter.  |
|        |                   |        |          |                           |                 |        | but only "" is  |
|        |                   |        |          |                           |                 |        | allowed.        |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| d      | off (0b00)        | None   | binary   | 11000 0b01: on            | 0b0             | None   | valid rules des |
|        |                   |        |          | 11000 0b00: off           |                 |        | cribed with bin |
|        |                   |        |          |                           |                 |        | ary masks       |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
| m1     | 2.3               | sec    | float    | None                      | None            | None   | a different par |
|        |                   |        |          |                           |                 |        | am in metadata  |
+--------+-------------------+--------+----------+---------------------------+-----------------+--------+-----------------+
MetaData-listeners = ListnerSet{}}

CompositeDataset-datasets =

#     [ dataset 1 ]
# ArrayDataset
description= {'arraydset 1'},
meta= {(No parameter.)MetaData-listeners = ListnerSet{}},
type= {None},
default= {None},
typecode= {None},
unit= {'ev'}
ArrayDataset-dataset =
768  4.4  5400

#     [ dataset 2 ]
# TableDataset
description= {'Example table'},
meta= {(No parameter.)MetaData-listeners = ListnerSet{}}
TableDataset-dataset =
   Time    Energy
  (sec)      (eV)
-------  --------
      0       100
      1       102
      2       104
      3       106
      4       108


level 1, repr
# CompositeDataset
description= {'test CD'},
meta= {
-------------  -----------------  ----------------
a= 3.4         b= xy (2019-02-19  c= Invalid (IJK)
               01:02:03.456789
               1929229323456789)
d= off (0b00)  m1= 2.3
-------------  -----------------  ----------------
MetaData-listeners = ListnerSet{}
}

CompositeDataset-datasets =

#     [ dataset 1 ]
# ArrayDataset
description= {'arraydset 1'},
meta= {(No parameter.)MetaData-listeners = ListnerSet{}
},
type= {None},
default= {None},
typecode= {None},
unit= {'ev'}
ArrayDataset-dataset =
768  4.4  5400

#     [ dataset 2 ]
# TableDataset
description= {'Example table'},
meta= {(No parameter.)MetaData-listeners = ListnerSet{}
}
TableDataset-dataset =
   Time    Energy
  (sec)      (eV)
-------  --------
      0       100
      1       102
      2       104
      3       106
      4       108


level 2,
# CompositeDataset
description, meta

CompositeDataset-datasets =

#     [ dataset 1 ]
ArrayDataset{ [768, 4.4, 5400.0] (ev) <None>, "arraydset 1", default None, tcode=None, meta=(No parameter.)MetaData-listeners = ListnerSet{}}
#     [ dataset 2 ]
# TableDataset
description, meta
TableDataset-dataset =
   Time    Energy
  (sec)      (eV)
-------  --------
      0       100
      1       102

(Only display 2 rows of 5 for level=2.)
"""
