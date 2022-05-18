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
│   ├── a_reference                             <ProductRef>
│   │   └── urnobj                                     <Urn>
│   │       └── urn                                    <str>
│   └── a_different_name                        <ProductRef>
├── history                                        <History>
│   ├── meta                                      <MetaData>
│   │   └── listeners                           <ListnerSet>
│   ├── args                             <ArrayDataset> (0,)
│   └── kw_args                        <TableDataset> (2, 0)
│       ├── meta                                  <MetaData>
│       │   └── listeners                       <ListnerSet>
│       ├── name                               <Column> (0,)
│       └── value                              <Column> (0,)
└── listeners                                   <ListnerSet>
├── meta                                          <MetaData>
│   ├── description                                 <string>
│   │   ├── description                                <str>
│   │   ├── default                                    <str>
│   │   ├── value                                      <str>
│   │   ├── valid                                 <NoneType>
│   │   └── typecode                                   <str>
│   ├── type                                        <string>
│   │   ├── description                                <str>
│   │   ├── default                                    <str>
│   │   ├── value                                      <str>
│   │   ├── valid                                 <NoneType>
│   │   └── typecode                                   <str>
│   ├── level                                       <string>
│   │   ├── description                                <str>
│   │   ├── default                                    <str>
│   │   ├── value                                      <str>
│   │   ├── valid                                 <NoneType>
│   │   └── typecode                                   <str>
│   ├── creator                                     <string>
│   │   ├── description                                <str>
│   │   ├── default                                    <str>
│   │   ├── value                                      <str>
│   │   ├── valid                                 <NoneType>
│   │   └── typecode                                   <str>
│   ├── creationDate                              <finetime>
│   │   ├── description                                <str>
│   │   ├── default                               <FineTime>
│   │   │   ├── tai                                    <int>
│   │   │   └── format                                 <str>
│   │   ├── value                                 <FineTime>
│   │   │   ├── tai                                    <int>
│   │   │   └── format                                 <str>
│   │   ├── valid                                 <NoneType>
│   │   └── typecode                                   <str>
│   ├── rootCause                                   <string>
│   │   ├── description                                <str>
│   │   ├── default                                    <str>
│   │   ├── value                                      <str>
│   │   ├── valid                                 <NoneType>
│   │   └── typecode                                   <str>
│   ├── version                                     <string>
│   │   ├── description                                <str>
│   │   ├── default                                    <str>
│   │   ├── value                                      <str>
│   │   ├── valid                                 <NoneType>
│   │   └── typecode                                   <str>
│   ├── FORMATV                                     <string>
│   │   ├── description                                <str>
│   │   ├── default                                    <str>
│   │   ├── value                                      <str>
│   │   ├── valid                                 <NoneType>
│   │   └── typecode                                   <str>
│   ├── speed                                       <vector>
│   │   ├── description                                <str>
│   │   ├── type                                       <str>
│   │   ├── default                               <NoneType>
│   │   ├── value                                   <Vector>
│   │   │   ├── components                            <list>
│   │   │   ├── unit                              <NoneType>
│   │   │   └── typecode                          <NoneType>
│   │   ├── valid                                     <list>
│   │   │   ├── 0                                     <list>
│   │   │   │   └── 0                                 <list>
│   │   │   └── 1                                     <list>
│   │   │       └── 0                                 <list>
│   │   ├── unit                                       <str>
│   │   └── typecode                              <NoneType>
│   └── listeners                               <ListnerSet>
├── measurements                          <CompositeDataset>
│   ├── meta                                      <MetaData>
│   │   └── listeners                           <ListnerSet>
│   ├── Time_Energy_Pos               <TableDataset> (5, 20)
│   │   ├── meta                                  <MetaData>
│   │   │   ├── description                         <string>
│   │   │   │   ├── description                        <str>
│   │   │   │   ├── default                            <str>
│   │   │   │   ├── value                              <str>
│   │   │   │   ├── valid                         <NoneType>
│   │   │   │   └── typecode                           <str>
│   │   │   ├── shape                                <tuple>
│   │   │   │   ├── description                        <str>
│   │   │   │   ├── type                               <str>
│   │   │   │   ├── default                          <tuple>
│   │   │   │   ├── value                            <tuple>
│   │   │   │   ├── valid                         <NoneType>
│   │   │   │   └── listeners                   <ListnerSet>
│   │   │   ├── type                                <string>
│   │   │   │   ├── description                        <str>
│   │   │   │   ├── default                            <str>
│   │   │   │   ├── value                              <str>
│   │   │   │   ├── valid                         <NoneType>
│   │   │   │   └── typecode                           <str>
│   │   │   ├── version                             <string>
│   │   │   │   ├── description                        <str>
│   │   │   │   ├── default                            <str>
│   │   │   │   ├── value                              <str>
│   │   │   │   ├── valid                         <NoneType>
│   │   │   │   └── typecode                           <str>
│   │   │   ├── FORMATV                             <string>
│   │   │   │   ├── description                        <str>
│   │   │   │   ├── default                            <str>
│   │   │   │   ├── value                              <str>
│   │   │   │   ├── valid                         <NoneType>
│   │   │   │   └── typecode                           <str>
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
│   ├── a_reference                             <ProductRef>
│   │   └── urnobj                                     <Urn>
│   │       └── urn                                    <str>
│   └── a_different_name                        <ProductRef>
├── history                                        <History>
│   ├── meta                                      <MetaData>
│   │   └── listeners                           <ListnerSet>
│   ├── args                             <ArrayDataset> (0,)
│   └── kw_args                        <TableDataset> (2, 0)
│       ├── meta                                  <MetaData>
│       │   ├── description                         <string>
│       │   │   ├── description                        <str>
│       │   │   ├── default                            <str>
│       │   │   ├── value                              <str>
│       │   │   ├── valid                         <NoneType>
│       │   │   └── typecode                           <str>
│       │   ├── shape                                <tuple>
│       │   │   ├── description                        <str>
│       │   │   ├── type                               <str>
│       │   │   ├── default                          <tuple>
│       │   │   ├── value                            <tuple>
│       │   │   ├── valid                         <NoneType>
│       │   │   └── listeners                   <ListnerSet>
│       │   ├── type                                <string>
│       │   │   ├── description                        <str>
│       │   │   ├── default                            <str>
│       │   │   ├── value                              <str>
│       │   │   ├── valid                         <NoneType>
│       │   │   └── typecode                           <str>
│       │   ├── version                             <string>
│       │   │   ├── description                        <str>
│       │   │   ├── default                            <str>
│       │   │   ├── value                              <str>
│       │   │   ├── valid                         <NoneType>
│       │   │   └── typecode                           <str>
│       │   ├── FORMATV                             <string>
│       │   │   ├── description                        <str>
│       │   │   ├── default                            <str>
│       │   │   ├── value                              <str>
│       │   │   ├── valid                         <NoneType>
│       │   │   └── typecode                           <str>
│       │   └── listeners                       <ListnerSet>
│       ├── name                               <Column> (0,)
│       └── value                              <Column> (0,)
└── listeners                                   <ListnerSet>
|__ meta                                          <MetaData>
|   |__ description                                 <string>
|   |   |__ description                                <str>
|   |   |__ default                                    <str>
|   |   |__ value                                      <str>
|   |   |__ valid                                 <NoneType>
|   |   \__ typecode                                   <str>
|   |__ type                                        <string>
|   |   |__ description                                <str>
|   |   |__ default                                    <str>
|   |   |__ value                                      <str>
|   |   |__ valid                                 <NoneType>
|   |   \__ typecode                                   <str>
|   |__ level                                       <string>
|   |   |__ description                                <str>
|   |   |__ default                                    <str>
|   |   |__ value                                      <str>
|   |   |__ valid                                 <NoneType>
|   |   \__ typecode                                   <str>
|   |__ creator                                     <string>
|   |   |__ description                                <str>
|   |   |__ default                                    <str>
|   |   |__ value                                      <str>
|   |   |__ valid                                 <NoneType>
|   |   \__ typecode                                   <str>
|   |__ creationDate                              <finetime>
|   |   |__ description                                <str>
|   |   |__ default                               <FineTime>
|   |   |   |__ tai                                    <int>
|   |   |   \__ format                                 <str>
|   |   |__ value                                 <FineTime>
|   |   |   |__ tai                                    <int>
|   |   |   \__ format                                 <str>
|   |   |__ valid                                 <NoneType>
|   |   \__ typecode                                   <str>
|   |__ rootCause                                   <string>
|   |   |__ description                                <str>
|   |   |__ default                                    <str>
|   |   |__ value                                      <str>
|   |   |__ valid                                 <NoneType>
|   |   \__ typecode                                   <str>
|   |__ version                                     <string>
|   |   |__ description                                <str>
|   |   |__ default                                    <str>
|   |   |__ value                                      <str>
|   |   |__ valid                                 <NoneType>
|   |   \__ typecode                                   <str>
|   |__ FORMATV                                     <string>
|   |   |__ description                                <str>
|   |   |__ default                                    <str>
|   |   |__ value                                      <str>
|   |   |__ valid                                 <NoneType>
|   |   \__ typecode                                   <str>
|   |__ speed                                       <vector>
|   |   |__ description                                <str>
|   |   |__ type                                       <str>
|   |   |__ default                               <NoneType>
|   |   |__ value                                   <Vector>
|   |   |   |__ components                            <list>
|   |   |   |__ unit                              <NoneType>
|   |   |   \__ typecode                          <NoneType>
|   |   |__ valid                                     <list>
|   |   |   |__ 0                                     <list>
|   |   |   |   \__ 0                                 <list>
|   |   |   \__ 1                                     <list>
|   |   |       \__ 0                                 <list>
|   |   |__ unit                                       <str>
|   |   \__ typecode                              <NoneType>
|   \__ listeners                               <ListnerSet>
|__ measurements                          <CompositeDataset>
|   |__ meta                                      <MetaData>
|   |   \__ listeners                           <ListnerSet>
|   |__ Time_Energy_Pos               <TableDataset> (5, 20)
|   |   |__ meta                                  <MetaData>
|   |   |   |__ description                         <string>
|   |   |   |   |__ description                        <str>
|   |   |   |   |__ default                            <str>
|   |   |   |   |__ value                              <str>
|   |   |   |   |__ valid                         <NoneType>
|   |   |   |   \__ typecode                           <str>
|   |   |   |__ shape                                <tuple>
|   |   |   |   |__ description                        <str>
|   |   |   |   |__ type                               <str>
|   |   |   |   |__ default                          <tuple>
|   |   |   |   |__ value                            <tuple>
|   |   |   |   |__ valid                         <NoneType>
|   |   |   |   \__ listeners                   <ListnerSet>
|   |   |   |__ type                                <string>
|   |   |   |   |__ description                        <str>
|   |   |   |   |__ default                            <str>
|   |   |   |   |__ value                              <str>
|   |   |   |   |__ valid                         <NoneType>
|   |   |   |   \__ typecode                           <str>
|   |   |   |__ version                             <string>
|   |   |   |   |__ description                        <str>
|   |   |   |   |__ default                            <str>
|   |   |   |   |__ value                              <str>
|   |   |   |   |__ valid                         <NoneType>
|   |   |   |   \__ typecode                           <str>
|   |   |   |__ FORMATV                             <string>
|   |   |   |   |__ description                        <str>
|   |   |   |   |__ default                            <str>
|   |   |   |   |__ value                              <str>
|   |   |   |   |__ valid                         <NoneType>
|   |   |   |   \__ typecode                           <str>
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
|   |__ a_reference                             <ProductRef>
|   |   \__ urnobj                                     <Urn>
|   |       \__ urn                                    <str>
|   \__ a_different_name                        <ProductRef>
|__ history                                        <History>
|   |__ meta                                      <MetaData>
|   |   \__ listeners                           <ListnerSet>
|   |__ args                             <ArrayDataset> (0,)
|   \__ kw_args                        <TableDataset> (2, 0)
|       |__ meta                                  <MetaData>
|       |   |__ description                         <string>
|       |   |   |__ description                        <str>
|       |   |   |__ default                            <str>
|       |   |   |__ value                              <str>
|       |   |   |__ valid                         <NoneType>
|       |   |   \__ typecode                           <str>
|       |   |__ shape                                <tuple>
|       |   |   |__ description                        <str>
|       |   |   |__ type                               <str>
|       |   |   |__ default                          <tuple>
|       |   |   |__ value                            <tuple>
|       |   |   |__ valid                         <NoneType>
|       |   |   \__ listeners                   <ListnerSet>
|       |   |__ type                                <string>
|       |   |   |__ description                        <str>
|       |   |   |__ default                            <str>
|       |   |   |__ value                              <str>
|       |   |   |__ valid                         <NoneType>
|       |   |   \__ typecode                           <str>
|       |   |__ version                             <string>
|       |   |   |__ description                        <str>
|       |   |   |__ default                            <str>
|       |   |   |__ value                              <str>
|       |   |   |__ valid                         <NoneType>
|       |   |   \__ typecode                           <str>
|       |   |__ FORMATV                             <string>
|       |   |   |__ description                        <str>
|       |   |   |__ default                            <str>
|       |   |   |__ value                              <str>
|       |   |   |__ valid                         <NoneType>
|       |   |   \__ typecode                           <str>
|       |   \__ listeners                       <ListnerSet>
|       |__ name                               <Column> (0,)
|       \__ value                              <Column> (0,)
\__ listeners                                   <ListnerSet>"""
