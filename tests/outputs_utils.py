# -*- coding: utf-8 -*-
out_tree = """tree out_tree
├── meta                                          <MetaData>
│   └── listeners                               <ListnerSet>
├── measurements                          <CompositeDataset>
│   ├── meta                                      <MetaData>
│   │   └── listeners                           <ListnerSet>
│   ├── Time_Energy_Pos               <TableDataset> (5, 20)
│   │   ├── meta                                  <MetaData>
│   │   │   └── listeners                       <ListnerSet>
│   │   ├── Time                              <Column> (20,)
│   │   ├── Energy                            <Column> (20,)
│   │   ├── Error                             <Column> (20,)
│   │   ├── y                                 <Column> (20,)
│   │   └── z                                 <Column> (20,)
│   ├── calibration                  <ArrayDataset> (11, 11)
│   └── dset                                           <str>
├── Environment Temperature              <ArrayDataset> (7,)
├── Browse                               <image/png> (5976,)
├── refs                                      <RefContainer>
│   └── a                                       <ProductRef>
├── history                                        <History>
│   ├── PARAM_HISTORY                                  <str>
│   ├── TASK_HISTORY                                   <str>
│   └── meta                                      <MetaData>
│       └── listeners                           <ListnerSet>
└── listeners                                   <ListnerSet>
├── meta                                          <MetaData>
│   ├── description                                 <string>
│   ├── type                                        <string>
│   ├── level                                       <string>
│   ├── creator                                     <string>
│   ├── creationDate                              <finetime>
│   ├── rootCause                                   <string>
│   ├── version                                     <string>
│   ├── FORMATV                                     <string>
│   ├── speed                                       <vector>
│   └── listeners                               <ListnerSet>
├── measurements                          <CompositeDataset>
│   ├── meta                                      <MetaData>
│   │   └── listeners                           <ListnerSet>
│   ├── Time_Energy_Pos               <TableDataset> (5, 20)
│   │   ├── meta                                  <MetaData>
│   │   │   ├── description                         <string>
│   │   │   ├── shape                                <tuple>
│   │   │   ├── type                                <string>
│   │   │   ├── version                             <string>
│   │   │   ├── FORMATV                             <string>
│   │   │   └── listeners                       <ListnerSet>
│   │   ├── Time                              <Column> (20,)
│   │   ├── Energy                            <Column> (20,)
│   │   ├── Error                             <Column> (20,)
│   │   ├── y                                 <Column> (20,)
│   │   └── z                                 <Column> (20,)
│   ├── calibration                  <ArrayDataset> (11, 11)
│   └── dset                                           <str>
├── Environment Temperature              <ArrayDataset> (7,)
├── Browse                               <image/png> (5976,)
├── refs                                      <RefContainer>
│   └── a                                       <ProductRef>
├── history                                        <History>
│   ├── PARAM_HISTORY                                  <str>
│   ├── TASK_HISTORY                                   <str>
│   └── meta                                      <MetaData>
│       └── listeners                           <ListnerSet>
└── listeners                                   <ListnerSet>
|__ meta                                          <MetaData>
|   |__ description                                 <string>
|   |__ type                                        <string>
|   |__ level                                       <string>
|   |__ creator                                     <string>
|   |__ creationDate                              <finetime>
|   |__ rootCause                                   <string>
|   |__ version                                     <string>
|   |__ FORMATV                                     <string>
|   |__ speed                                       <vector>
|   \__ listeners                               <ListnerSet>
|__ measurements                          <CompositeDataset>
|   |__ meta                                      <MetaData>
|   |   \__ listeners                           <ListnerSet>
|   |__ Time_Energy_Pos               <TableDataset> (5, 20)
|   |   |__ meta                                  <MetaData>
|   |   |   |__ description                         <string>
|   |   |   |__ shape                                <tuple>
|   |   |   |__ type                                <string>
|   |   |   |__ version                             <string>
|   |   |   |__ FORMATV                             <string>
|   |   |   \__ listeners                       <ListnerSet>
|   |   |__ Time                              <Column> (20,)
|   |   |__ Energy                            <Column> (20,)
|   |   |__ Error                             <Column> (20,)
|   |   |__ y                                 <Column> (20,)
|   |   \__ z                                 <Column> (20,)
|   |__ calibration                  <ArrayDataset> (11, 11)
|   \__ dset                                           <str>
|__ Environment Temperature              <ArrayDataset> (7,)
|__ Browse                               <image/png> (5976,)
|__ refs                                      <RefContainer>
|   \__ a                                       <ProductRef>
|__ history                                        <History>
|   |__ PARAM_HISTORY                                  <str>
|   |__ TASK_HISTORY                                   <str>
|   \__ meta                                      <MetaData>
|       \__ listeners                           <ListnerSet>
\__ listeners                                   <ListnerSet>"""
