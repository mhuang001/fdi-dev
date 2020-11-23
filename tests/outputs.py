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
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| name   | value             | unit   | type     | valid                | default         | code   | description       |
+========+===================+========+==========+======================+=================+========+===================+
| a      | 3.4               | None   | float    | (0, 31): valid       | 2.0             | None   | rule name, if is  |
|        |                   |        |          | 99:                  |                 |        | "valid", "", or " |
|        |                   |        |          |                      |                 |        | default", is ommi |
|        |                   |        |          |                      |                 |        | ted in value stri |
|        |                   |        |          |                      |                 |        | ng.               |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| b      | ever (2019-02-19  |        | finetime | [(0, 987654321012345 | 1958-01-01      |        | date param        |
|        | 01:02:03.456789   |        |          | 6): ever]            | 00:00:00.000099 |        |                   |
|        | 1929229323456789) |        |          |                      | 99              |        |                   |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| c      | Invalid (Right)   |        | string   | '': empty            | cliche          | B      | str parameter. bu |
|        |                   |        |          |                      |                 |        | t only "" is allo |
|        |                   |        |          |                      |                 |        | wed.              |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| d      | off (0b0)         | None   | binary   | (0b110, 0b1): on     | 0b0             | None   | valid rules descr |
|        |                   |        |          | (0b110, 0b0): off    |                 |        | ibed with binary  |
|        |                   |        |          |                      |                 |        | masks             |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
MetaData-listeners = ListnerSet{}}
GenericDataset-dataset =
88.8
level 1, repr
# GenericDataset
description= {'test GD'},
meta= {
------------  -------------------  ------------------
a= 3.4        b= ever (2019-02-19  c= Invalid (Right)
              01:02:03.456789
              1929229323456789)
d= off (0b0)
------------  -------------------  ------------------
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
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| name   | value             | unit   | type     | valid                | default         | code   | description       |
+========+===================+========+==========+======================+=================+========+===================+
| a      | 3.4               | None   | float    | (0, 31): valid       | 2.0             | None   | rule name, if is  |
|        |                   |        |          | 99:                  |                 |        | "valid", "", or " |
|        |                   |        |          |                      |                 |        | default", is ommi |
|        |                   |        |          |                      |                 |        | ted in value stri |
|        |                   |        |          |                      |                 |        | ng.               |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| b      | ever (2019-02-19  |        | finetime | [(0, 987654321012345 | 1958-01-01      |        | date param        |
|        | 01:02:03.456789   |        |          | 6): ever]            | 00:00:00.000099 |        |                   |
|        | 1929229323456789) |        |          |                      | 99              |        |                   |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| c      | Invalid (Right)   |        | string   | '': empty            | cliche          | B      | str parameter. bu |
|        |                   |        |          |                      |                 |        | t only "" is allo |
|        |                   |        |          |                      |                 |        | wed.              |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| d      | off (0b0)         | None   | binary   | (0b110, 0b1): on     | 0b0             | None   | valid rules descr |
|        |                   |        |          | (0b110, 0b0): off    |                 |        | ibed with binary  |
|        |                   |        |          |                      |                 |        | masks             |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
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
------------  -------------------  ------------------
a= 3.4        b= ever (2019-02-19  c= Invalid (Right)
              01:02:03.456789
              1929229323456789)
d= off (0b0)
------------  -------------------  ------------------
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
ArrayDataset{ [([0, 0, 0, 0, 0], [0, 0, 0, 0, 0]): [[0, 0, 0, 0, 0], [0, 0, 0, 1, 0], [5, 4, 3, 2, 1], [0, 0, 0, 3, 0]], ([0, 0, 0, 0, 0], [0, 0, 0, 0, 0]): [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]] (lyr) <None>, "toString tester AD", dflt None, tcode=None, meta=
------------  -------------------  ------------------
a= 3.4        b= ever (2019-02-19  c= Invalid (Right)
              01:02:03.456789
              1929229323456789)
d= off (0b0)
------------  -------------------  ------------------
MetaData-listeners = ListnerSet{}}"""
out_TableDataset = """level 0
# TableDataset
description= {'UNKNOWN'},
meta= {
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| name   | value             | unit   | type     | valid                | default         | code   | description       |
+========+===================+========+==========+======================+=================+========+===================+
| a      | 3.4               | None   | float    | (0, 31): valid       | 2.0             | None   | rule name, if is  |
|        |                   |        |          | 99:                  |                 |        | "valid", "", or " |
|        |                   |        |          |                      |                 |        | default", is ommi |
|        |                   |        |          |                      |                 |        | ted in value stri |
|        |                   |        |          |                      |                 |        | ng.               |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| b      | ever (2019-02-19  |        | finetime | [(0, 987654321012345 | 1958-01-01      |        | date param        |
|        | 01:02:03.456789   |        |          | 6): ever]            | 00:00:00.000099 |        |                   |
|        | 1929229323456789) |        |          |                      | 99              |        |                   |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| c      | Invalid (Right)   |        | string   | '': empty            | cliche          | B      | str parameter. bu |
|        |                   |        |          |                      |                 |        | t only "" is allo |
|        |                   |        |          |                      |                 |        | wed.              |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| d      | off (0b0)         | None   | binary   | (0b110, 0b1): on     | 0b0             | None   | valid rules descr |
|        |                   |        |          | (0b110, 0b0): off    |                 |        | ibed with binary  |
|        |                   |        |          |                      |                 |        | masks             |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
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
------------  -------------------  ------------------
a= 3.4        b= ever (2019-02-19  c= Invalid (Right)
              01:02:03.456789
              1929229323456789)
d= off (0b0)
------------  -------------------  ------------------
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
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| name   | value             | unit   | type     | valid                | default         | code   | description       |
+========+===================+========+==========+======================+=================+========+===================+
| a      | 3.4               | None   | float    | (0, 31): valid       | 2.0             | None   | rule name, if is  |
|        |                   |        |          | 99:                  |                 |        | "valid", "", or " |
|        |                   |        |          |                      |                 |        | default", is ommi |
|        |                   |        |          |                      |                 |        | ted in value stri |
|        |                   |        |          |                      |                 |        | ng.               |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| b      | ever (2019-02-19  |        | finetime | [(0, 987654321012345 | 1958-01-01      |        | date param        |
|        | 01:02:03.456789   |        |          | 6): ever]            | 00:00:00.000099 |        |                   |
|        | 1929229323456789) |        |          |                      | 99              |        |                   |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| c      | Invalid (Right)   |        | string   | '': empty            | cliche          | B      | str parameter. bu |
|        |                   |        |          |                      |                 |        | t only "" is allo |
|        |                   |        |          |                      |                 |        | wed.              |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| d      | off (0b0)         | None   | binary   | (0b110, 0b1): on     | 0b0             | None   | valid rules descr |
|        |                   |        |          | (0b110, 0b0): off    |                 |        | ibed with binary  |
|        |                   |        |          |                      |                 |        | masks             |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
| m1     | 2.3               | sec    | float    | None                 | None            | None   | a different param |
|        |                   |        |          |                      |                 |        |  in metadata      |
+--------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
MetaData-listeners = ListnerSet{}}

CompositeDataset-datasets =

#     [ dataset 1 ]
# ArrayDataset
description= {'arraydset 1'},
meta= {
(empty)
MetaData-listeners = ListnerSet{}},
type= {None},
default= {None},
typecode= {None},
unit= {'ev'}
ArrayDataset-dataset =
768  4.4  5400

#     [ dataset 2 ]
# TableDataset
description= {'Example table'},
meta= {
(empty)
MetaData-listeners = ListnerSet{}}
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
------------  -------------------  ------------------
a= 3.4        b= ever (2019-02-19  c= Invalid (Right)
              01:02:03.456789
              1929229323456789)
d= off (0b0)  m1= 2.3
------------  -------------------  ------------------
MetaData-listeners = ListnerSet{}
}

CompositeDataset-datasets =

#     [ dataset 1 ]
# ArrayDataset
description= {'arraydset 1'},
meta= {
(empty)
MetaData-listeners = ListnerSet{}
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
meta= {
(empty)
MetaData-listeners = ListnerSet{}
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
ArrayDataset{ [768, 4.4, 5400.0] (ev) <None>, "arraydset 1", dflt None, tcode=None, meta=
(empty)
MetaData-listeners = ListnerSet{}}
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
