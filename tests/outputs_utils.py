# -*- coding: utf-8 -*-
out_tree = """tree out_tree
├── meta                                          <MetaData>
│   └── listeners                              <ListenerSet>
├── measurements                          <CompositeDataset>
│   ├── meta                                      <MetaData>
│   │   └── listeners                          <ListenerSet>
│   ├── Time_Energy_Pos               <TableDataset> [5, 20]
│   │   ├── meta                                  <MetaData>
│   │   │   └── listeners                      <ListenerSet>
│   │   ├── Time                               <Column> [20]
│   │   ├── Energy                             <Column> [20]
│   │   ├── Error                              <Column> [20]
│   │   ├── y                                  <Column> [20]
│   │   └── z                                  <Column> [20]
│   ├── calibration                  <ArrayDataset> [11, 11]
│   └── dset                                           <str>
├── Environment Temperature               <ArrayDataset> [7]
├── Browse                                <image/png> [5976]
├── refs                                      <RefContainer>
│   ├── a_reference                             <ProductRef>
│   │   └── urnobj                                     <Urn>
│   │       └── urn                                    <str>
│   └── a_different_name                        <ProductRef>
├── history                            <TableDataset> [2, 0]
│   ├── meta                                      <MetaData>
│   │   └── listeners                          <ListenerSet>
│   ├── name                                    <Column> [0]
│   └── reference                               <Column> [0]
└── listeners                                  <ListenerSet>
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
│   └── listeners                              <ListenerSet>
├── measurements                          <CompositeDataset>
│   ├── meta                                      <MetaData>
│   │   └── listeners                          <ListenerSet>
│   ├── Time_Energy_Pos               <TableDataset> [5, 20]
│   │   ├── meta                                  <MetaData>
│   │   │   ├── description                         <string>
│   │   │   │   ├── description                        <str>
│   │   │   │   ├── default                            <str>
│   │   │   │   ├── value                              <str>
│   │   │   │   ├── valid                         <NoneType>
│   │   │   │   └── typecode                           <str>
│   │   │   ├── shape                                 <list>
│   │   │   │   ├── description                        <str>
│   │   │   │   ├── type                               <str>
│   │   │   │   ├── default                           <list>
│   │   │   │   ├── value                             <list>
│   │   │   │   ├── valid                         <NoneType>
│   │   │   │   ├── unit                               <str>
│   │   │   │   └── typecode                           <str>
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
│   │   │   └── listeners                      <ListenerSet>
│   │   ├── Time                               <Column> [20]
│   │   ├── Energy                             <Column> [20]
│   │   ├── Error                              <Column> [20]
│   │   ├── y                                  <Column> [20]
│   │   └── z                                  <Column> [20]
│   ├── calibration                  <ArrayDataset> [11, 11]
│   └── dset                                           <str>
├── Environment Temperature               <ArrayDataset> [7]
├── Browse                                <image/png> [5976]
├── refs                                      <RefContainer>
│   ├── a_reference                             <ProductRef>
│   │   └── urnobj                                     <Urn>
│   │       └── urn                                    <str>
│   └── a_different_name                        <ProductRef>
├── history                            <TableDataset> [2, 0]
│   ├── meta                                      <MetaData>
│   │   ├── description                             <string>
│   │   │   ├── description                            <str>
│   │   │   ├── default                                <str>
│   │   │   ├── value                                  <str>
│   │   │   ├── valid                             <NoneType>
│   │   │   └── typecode                               <str>
│   │   ├── shape                                     <list>
│   │   │   ├── description                            <str>
│   │   │   ├── type                                   <str>
│   │   │   ├── default                               <list>
│   │   │   ├── value                                 <list>
│   │   │   ├── valid                             <NoneType>
│   │   │   ├── unit                                   <str>
│   │   │   └── typecode                               <str>
│   │   ├── type                                    <string>
│   │   │   ├── description                            <str>
│   │   │   ├── default                                <str>
│   │   │   ├── value                                  <str>
│   │   │   ├── valid                             <NoneType>
│   │   │   └── typecode                               <str>
│   │   ├── version                                 <string>
│   │   │   ├── description                            <str>
│   │   │   ├── default                                <str>
│   │   │   ├── value                                  <str>
│   │   │   ├── valid                             <NoneType>
│   │   │   └── typecode                               <str>
│   │   ├── FORMATV                                 <string>
│   │   │   ├── description                            <str>
│   │   │   ├── default                                <str>
│   │   │   ├── value                                  <str>
│   │   │   ├── valid                             <NoneType>
│   │   │   └── typecode                               <str>
│   │   └── listeners                          <ListenerSet>
│   ├── name                                    <Column> [0]
│   └── reference                               <Column> [0]
└── listeners                                  <ListenerSet>
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
|   \__ listeners                              <ListenerSet>
|__ measurements                          <CompositeDataset>
|   |__ meta                                      <MetaData>
|   |   \__ listeners                          <ListenerSet>
|   |__ Time_Energy_Pos               <TableDataset> [5, 20]
|   |   |__ meta                                  <MetaData>
|   |   |   |__ description                         <string>
|   |   |   |   |__ description                        <str>
|   |   |   |   |__ default                            <str>
|   |   |   |   |__ value                              <str>
|   |   |   |   |__ valid                         <NoneType>
|   |   |   |   \__ typecode                           <str>
|   |   |   |__ shape                                 <list>
|   |   |   |   |__ description                        <str>
|   |   |   |   |__ type                               <str>
|   |   |   |   |__ default                           <list>
|   |   |   |   |__ value                             <list>
|   |   |   |   |__ valid                         <NoneType>
|   |   |   |   |__ unit                               <str>
|   |   |   |   \__ typecode                           <str>
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
|   |   |   \__ listeners                      <ListenerSet>
|   |   |__ Time                               <Column> [20]
|   |   |__ Energy                             <Column> [20]
|   |   |__ Error                              <Column> [20]
|   |   |__ y                                  <Column> [20]
|   |   \__ z                                  <Column> [20]
|   |__ calibration                  <ArrayDataset> [11, 11]
|   \__ dset                                           <str>
|__ Environment Temperature               <ArrayDataset> [7]
|__ Browse                                <image/png> [5976]
|__ refs                                      <RefContainer>
|   |__ a_reference                             <ProductRef>
|   |   \__ urnobj                                     <Urn>
|   |       \__ urn                                    <str>
|   \__ a_different_name                        <ProductRef>
|__ history                            <TableDataset> [2, 0]
|   |__ meta                                      <MetaData>
|   |   |__ description                             <string>
|   |   |   |__ description                            <str>
|   |   |   |__ default                                <str>
|   |   |   |__ value                                  <str>
|   |   |   |__ valid                             <NoneType>
|   |   |   \__ typecode                               <str>
|   |   |__ shape                                     <list>
|   |   |   |__ description                            <str>
|   |   |   |__ type                                   <str>
|   |   |   |__ default                               <list>
|   |   |   |__ value                                 <list>
|   |   |   |__ valid                             <NoneType>
|   |   |   |__ unit                                   <str>
|   |   |   \__ typecode                               <str>
|   |   |__ type                                    <string>
|   |   |   |__ description                            <str>
|   |   |   |__ default                                <str>
|   |   |   |__ value                                  <str>
|   |   |   |__ valid                             <NoneType>
|   |   |   \__ typecode                               <str>
|   |   |__ version                                 <string>
|   |   |   |__ description                            <str>
|   |   |   |__ default                                <str>
|   |   |   |__ value                                  <str>
|   |   |   |__ valid                             <NoneType>
|   |   |   \__ typecode                               <str>
|   |   |__ FORMATV                                 <string>
|   |   |   |__ description                            <str>
|   |   |   |__ default                                <str>
|   |   |   |__ value                                  <str>
|   |   |   |__ valid                             <NoneType>
|   |   |   \__ typecode                               <str>
|   |   \__ listeners                          <ListenerSet>
|   |__ name                                    <Column> [0]
|   \__ reference                               <Column> [0]
\__ listeners                                  <ListenerSet>"""
