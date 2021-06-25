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
=== GenericDataset () ===
meta= {
======  ====================  ======  ========  ====================  =================  ======  =====================
name    value                 unit    type      valid                 default            code    description
======  ====================  ======  ========  ====================  =================  ======  =====================
a       3.4                   None    float     (0, 31): valid        2.0                None    rule name, if is "val
                                                99:                                              id", "", or "default"
                                                                                                 , is ommited in value
                                                                                                  string.
b       xy (2019-02-19T01:02          finetime  (0, 9876543210123456  1958-01-01T00:00:  Q       date param
        :03.456789                              ): xy                 00.000099
        1929229360456789)                                             99
c       Invalid (IJK)                 string    '': empty             cliche             B       this is a string para
                                                                                                 meter. but only "" is
                                                                                                  allowed.
d       off (0b00)            None    binary    11000 0b01: on        0b0                H       valid rules described
                                                11000 0b00: off                                   with binary masks
======  ====================  ======  ========  ====================  =================  ======  =====================
MetaData-listeners = ListnerSet{}}
GenericDataset-dataset =
88.8
level 1, repr
=== GenericDataset () ===
meta= {
-------------  --------------------------  ----------------
a= 3.4         b= xy (2019-02-19T01:02:03  c= Invalid (IJK)
               .456789
               1929229360456789)
d= off (0b00)
-------------  --------------------------  ----------------
MetaData-listeners = ListnerSet{}
}
GenericDataset-dataset =
88.8
level 2,
GenericDataset{ 88.8, description = "test GD", meta = a=3.4, b=xy (FineTime(2019-02-19T01:02:03.456789)), c=Invalid (IJK), d=off (0b00). }"""
out_ArrayDataset = """

level 0
=== ArrayDataset () ===
meta= {
===============  ====================  ======  ========  ====================  =================  ======  =====================
name             value                 unit    type      valid                 default            code    description
===============  ====================  ======  ========  ====================  =================  ======  =====================
description      toString tester AD            string    None                  UNKNOWN            B       Description of this d
                                                                                                          ataset
unit             lyr                           string    None                  None               B       Unit of every element
                                                                                                          .
shape            ()                            tuple     None                  ()                         Number of elements in
                                                                                                           each dimension. Quic
                                                                                                          k changers to the rig
                                                                                                          ht.
typecode         UNKNOWN                       string    None                  UNKNOWN            B       Python internal stora
                                                                                                          ge code.
version          0.1                           string    None                  0.1                B       Version of dataset
FORMATV          1.6.0.1                       string    None                  1.6.0.1            B       Version of dataset sc
                                                                                                          hema and revision
a                3.4                   None    float     (0, 31): valid        2.0                None    rule name, if is "val
                                                         99:                                              id", "", or "default"
                                                                                                          , is ommited in value
                                                                                                           string.
b                xy (2019-02-19T01:02          finetime  (0, 9876543210123456  1958-01-01T00:00:  Q       date param
                 :03.456789                              ): xy                 00.000099
                 1929229360456789)                                             99
c                Invalid (IJK)                 string    '': empty             cliche             B       this is a string para
                                                                                                          meter. but only "" is
                                                                                                           allowed.
d                off (0b00)            None    binary    11000 0b01: on        0b0                H       valid rules described
                                                         11000 0b00: off                                   with binary masks
added_parameter  42                    None    integer   None                  None               None    A non-builtin param
===============  ====================  ======  ========  ====================  =================  ======  =====================
MetaData-listeners = ListnerSet{}}
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




level 1
=== ArrayDataset () ===
meta= {
--------------------------  --------------------------  ----------------
description= toString test  unit= lyr                   shape= ()
er AD
typecode= UNKNOWN           version= 0.1                FORMATV= 1.6.0.1
a= 3.4                      b= xy (2019-02-19T01:02:03  c= Invalid (IJK)
                            .456789
                            1929229360456789)
d= off (0b00)               added_parameter= 42
--------------------------  --------------------------  ----------------
MetaData-listeners = ListnerSet{}
}
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




level 2, repr
ArrayDataset(description=toString tester AD, unit=lyr, a=3.4, b=xy (FineTime(2019-02-19T01:02:03.456789)), c=Invalid (IJK), d=off (0b00), added_parameter=42. data= [[[[0, 0, 0, ...0]]], [[[0, 0, 0, ...0]]]])

an empty meta and long data level 2: 
ArrayDataset(Default Meta. data= [8, 8, 8, 8, 8, 8, 8, 8])

"""
out_TableDataset = """

level 0
=== TableDataset () ===
meta= {
===============  ====================  ======  ========  ====================  =================  ======  =====================
name             value                 unit    type      valid                 default            code    description
===============  ====================  ======  ========  ====================  =================  ======  =====================
description      UNKNOWN                       string    None                  UNKNOWN            B       Description of this d
                                                                                                          ataset
version          0.1                           string    None                  0.1                B       Version of dataset
FORMATV          1.6.0.1                       string    None                  1.6.0.1            B       Version of dataset sc
                                                                                                          hema and revision
a                3.4                   None    float     (0, 31): valid        2.0                None    rule name, if is "val
                                                         99:                                              id", "", or "default"
                                                                                                          , is ommited in value
                                                                                                           string.
b                xy (2019-02-19T01:02          finetime  (0, 9876543210123456  1958-01-01T00:00:  Q       date param
                 :03.456789                              ): xy                 00.000099
                 1929229360456789)                                             99
c                Invalid (IJK)                 string    '': empty             cliche             B       this is a string para
                                                                                                          meter. but only "" is
                                                                                                           allowed.
d                off (0b00)            None    binary    11000 0b01: on        0b0                H       valid rules described
                                                         11000 0b00: off                                   with binary masks
added_parameter  42                    None    integer   None                  None               None    A non-builtin param
===============  ====================  ======  ========  ====================  =================  ======  =====================
MetaData-listeners = ListnerSet{}}
TableDataset-dataset =
  col1     col2
  (eV)    (cnt)
------  -------
   1        0
   4.4     43.2
5400     2000




level 1
=== TableDataset () ===
meta= {
--------------------  --------------------------  ----------------
description= UNKNOWN  version= 0.1                FORMATV= 1.6.0.1
a= 3.4                b= xy (2019-02-19T01:02:03  c= Invalid (IJK)
                      .456789
                      1929229360456789)
d= off (0b00)         added_parameter= 42
--------------------  --------------------------  ----------------
MetaData-listeners = ListnerSet{}
}
TableDataset-dataset =
  col1     col2
  (eV)    (cnt)
------  -------
   1        0
   4.4     43.2
5400     2000




level 2, repr
TableDataset(a=3.4, b=xy (FineTime(2019-02-19T01:02:03.456789)), c=Invalid (IJK), d=off (0b00), added_parameter=42.data= {"col1": Column(description=1, unit=eV. data= [1, 4.4, 5400.0]), "col2": Column(description=2, unit=cnt. data= [0, 43.2, 2000.0])})

an empty level 2: 
TableDataset(Default Meta.data= {})

"""
out_CompositeDataset = """level 0
=== CompositeDataset () ===
meta= {
======  ====================  ======  ========  ====================  =================  ======  =====================
name    value                 unit    type      valid                 default            code    description
======  ====================  ======  ========  ====================  =================  ======  =====================
a       3.4                   None    float     (0, 31): valid        2.0                None    rule name, if is "val
                                                99:                                              id", "", or "default"
                                                                                                 , is ommited in value
                                                                                                  string.
b       xy (2019-02-19T01:02          finetime  (0, 9876543210123456  1958-01-01T00:00:  Q       date param
        :03.456789                              ): xy                 00.000099
        1929229360456789)                                             99
c       Invalid (IJK)                 string    '': empty             cliche             B       this is a string para
                                                                                                 meter. but only "" is
                                                                                                  allowed.
d       off (0b00)            None    binary    11000 0b01: on        0b0                H       valid rules described
                                                11000 0b00: off                                   with binary masks
m1      2.3                   sec     float     None                  None               None    a different param in
                                                                                                 metadata
======  ====================  ======  ========  ====================  =================  ======  =====================
MetaData-listeners = ListnerSet{}}

CompositeDataset-datasets =
<ODict "dataset 1":
=== ArrayDataset () ===
meta= {
===========  ===========  ======  ======  =======  =========  ======  =====================
name         value        unit    type    valid    default    code    description
===========  ===========  ======  ======  =======  =========  ======  =====================
description  arraydset 1          string  None     UNKNOWN    B       Description of this d
                                                                      ataset
unit         ev                   string  None     None       B       Unit of every element
                                                                      .
shape        ()                   tuple   None     ()                 Number of elements in
                                                                       each dimension. Quic
                                                                      k changers to the rig
                                                                      ht.
typecode     UNKNOWN              string  None     UNKNOWN    B       Python internal stora
                                                                      ge code.
version      0.1                  string  None     0.1        B       Version of dataset
FORMATV      1.6.0.1              string  None     1.6.0.1    B       Version of dataset sc
                                                                      hema and revision
===========  ===========  ======  ======  =======  =========  ======  =====================
MetaData-listeners = ListnerSet{}}
ArrayDataset-dataset =
768  4.4  5400
"dataset 2":
=== TableDataset () ===
meta= {
===========  =============  ======  ======  =======  =========  ======  =====================
name         value          unit    type    valid    default    code    description
===========  =============  ======  ======  =======  =========  ======  =====================
description  Example table          string  None     UNKNOWN    B       Description of this d
                                                                        ataset
version      0.1                    string  None     0.1        B       Version of dataset
FORMATV      1.6.0.1                string  None     1.6.0.1    B       Version of dataset sc
                                                                        hema and revision
===========  =============  ======  ======  =======  =========  ======  =====================
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


>level 1, repr
=== CompositeDataset () ===
meta= {
-------------  --------------------------  ----------------
a= 3.4         b= xy (2019-02-19T01:02:03  c= Invalid (IJK)
               .456789
               1929229360456789)
d= off (0b00)  m1= 2.3
-------------  --------------------------  ----------------
MetaData-listeners = ListnerSet{}
}

CompositeDataset-datasets =
<ODict  === ArrayDataset () ===
meta= {
------------------------  ------------  ----------------
description= arraydset 1  unit= ev      shape= ()
typecode= UNKNOWN         version= 0.1  FORMATV= 1.6.0.1
------------------------  ------------  ----------------
MetaData-listeners = ListnerSet{}
}
ArrayDataset-dataset =
768  4.4  5400
 === TableDataset () ===
meta= {
--------------------------  ------------  ----------------
description= Example table  version= 0.1  FORMATV= 1.6.0.1
--------------------------  ------------  ----------------
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


>level 2,
=== CompositeDataset () ===
meta

CompositeDataset-datasets =
<ODict  ArrayDataset(description=arraydset 1, unit=ev. data= [768, 4.4, 5400.0]) TableDataset(description=Example table.data= {"Time": Column(unit=sec. data= [0.0, 1.0, 2.0, 3.0, 4.0]), "Energy": Column(unit=eV. data= [100.0, 102.0, 104.0, 106.0, 108.0])})>"""
out_FineTime = """toString test
=========== format: "%Y-%m-%dT%H:%M:%S.%f" =======
FineTime
level=0 width=0: 2019-02-19T01:02:03.456789 TAI(1929229360456789) format=%Y-%m-%dT%H:%M:%S.%f
level=1 width=0: 2019-02-19T01:02:03.456789 (1929229360456789)
level=2 width=0: FineTime(2019-02-19T01:02:03.456789)
level=0 width=1: 2019-02-19T01:02:03.456789
1929229360456789
level=1 width=1: 2019-02-19T01:02:03.456789
1929229360456789
level=2 width=1: FineTime(2019-02-19
01:02:03.456789)
FineTime1
level=0 width=0: 2019-02-19T01:02:03.457000 TAI(67309323457) format=%Y-%m-%dT%H:%M:%S.%f
level=1 width=0: 2019-02-19T01:02:03.457000 (67309323457)
level=2 width=0: FineTime1(2019-02-19T01:02:03.457000)
level=0 width=1: 2019-02-19T01:02:03.457000
67309323457
level=1 width=1: 2019-02-19T01:02:03.457000
67309323457
level=2 width=1: FineTime1(2019-02-19
01:02:03.457000)
=========== format: "%Y" =======
FineTime
level=0 width=0: 2019 TAI(1929229360456789) format=%Y
level=1 width=0: 2019 (1929229360456789)
level=2 width=0: FineTime(2019)
level=0 width=1: 2019
1929229360456789
level=1 width=1: 2019
1929229360456789
level=2 width=1: FineTime(2019)
FineTime1
level=0 width=0: 2019 TAI(67309323457) format=%Y
level=1 width=0: 2019 (67309323457)
level=2 width=0: FineTime1(2019)
level=0 width=1: 2019
67309323457
level=1 width=1: 2019
67309323457
level=2 width=1: FineTime1(2019)
"""
