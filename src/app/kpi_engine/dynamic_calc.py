
import random
from src.app.kpi_engine.kpi_request import KPIRequest
from src.app.kpi_engine.kpi_response import KPIResponse
from src.app.models import RealTimeData, AggregatedKPI

from sqlalchemy.orm import Session
import requests
import re
import pandas as pd
import numpy as np
import numexpr
from datetime import datetime


['A°sum°mo[ S°/[ R°consumption_sum°T°m°o° ; R°time_sum°T°m°o° ]]',
  'A°sum°mo[ A°sum°t[ D°consumption_sum°t°m°o° ] ]', 
  'A°sum°mo[ A°sum°t[ D°time_sum°t°m°o° ]]']


nome='power_cumulative'
kpi = ""
kpi_list = {'power_cumulative':"A°mean°mo[S°/[R°consumption_sum°T°m°o;R°time_sum°T°m°o]]",'consumption_sum':"A°sum°mo[A°sum°t[D°consumption_sum°T°m°o]]", 'time_sum':'A°sum°mo[A°sum°t[D°time_sum°t°m°o°]]'}
partial={}


def preprocessing():
    #preparazione che avviene fuori
    kpi=kpi_list[nome]
    #prendiamo la variabile su cui si aggrega
    serach_var=kpi.split('°')
    var=serach_var[2].split('[')
    partial['var']=var[0]
    partial['agg']=serach_var[1]



def KPI_calculate(kpi, kpi_list,partial,db:Session,start_date,end_date,machine,step):

    pattern = re.compile(r'\[([^\[\]]*)\]')
    match = pattern.search(kpi)

    if match:
        inner_content = match.group(0)
        print("\n")
        #inner_content = re.sub(r'\[|\]', '', inner_content)
        print("Processing: ", inner_content)
    
        output=[]
        if ';' in inner_content:
            parts = inner_content.split(';')
            for part in parts:
                part = re.sub(r'\[|\]', '', part)
                result = KPI_calculate(part, kpi_list,partial)
                output.append(result)
        else:
            part = re.sub(r'\[|\]', '', inner_content)
            result = KPI_calculate(part, kpi_list,partial)
            output.append(result)


        remaining_string = kpi.replace(inner_content, str(','.join(map(str, output))), 1)
        print("Remaining string: ", remaining_string)        
        result = KPI_calculate(remaining_string, kpi_list,partial) 
        
        return result
    else:
        kpi = re.sub(r'\[|\]', '', kpi)
        print("Processing base case: ", kpi)
        operation = kpi[0]
        print(operation)
        if operation in ['S', 'A', 'R', 'D','°','C']:
            if operation == 'S':

                return S_operation(kpi,partial)

            elif operation == 'A':

                return A_aggregation(kpi,partial)
                

            elif operation == 'R':

                #i check for the kpi
                kpi_split=kpi.split('°')
                kpi_involved=kpi_split[1]
                print("kpi coinvoloto "+kpi_involved)


                #check if the string is in other formula
                if kpi_involved in kpi_list:
                    return str(KPI_calculate(kpi_list[kpi_involved],kpi_list,partial))
                #trovo la corrispondernza
                else:
                    return '°no'
                
                      
            elif operation == 'D':

                #devo fare la query
                #a=dataframe
                dataframe=query_DB(db,start_date,end_date,machine,operation,kpi,step)
                
                key=random.randint(1, 100)

                key=str(key)

                #controllo che la chiave non sia presa
                while True:
                    if key in partial:
                        key=random.randint(1, 100)
                        key=str(key)
                    else:
                        break

                #inserisco il valore all'interno del dataframe dei valori parziali
                partial[key]=dataframe

                print(partial)
                return "°"+key
            
            #caso in cui incontro una costante
            elif operation == 'C':

                #genero una chiave 
                key=random.randint(1, 100)
                key=str(key)

                #controllo che la chiave non sia presa
                while True:
                    if key in partial:
                        key=random.randint(1, 100)
                        key=str(key)
                    else:
                        break
                
                div=kpi.split('°')

                partial[key]=int(div[1])

                return "°"+key
            
            elif operation=='°':
                chiave=kpi.replace('°','')
                result=getattr(np,partial['agg'])(partial[chiave],axis=0)
                return str(result)
            
                
                


#scrivo funzione di gestione
#facciamo che ho trovato D quindi devo andare a controllare il database
#i need to do the query with the values that i have so the ones that came from the request of the RAG
def query_DB(db:Session,start_date,end_date,machine,operation,stringa,step):
        
        #prendo la stringa
        lista_stringa= stringa.split('°')
        match = re.search(r'^(.*)_(.+)$', lista_stringa[1])
        if match:
            before_last_underscore = match.group(1)
            after_last_underscore = match.group(2)

    # SELECT kpi, time,machine_operation value FROM RealTimeData
        # WHERE kpi IN (involved_kpis)
        # AND machine = machine
        # and operation= operation
        # AND time between start_date, end_date
        raw_query_statement = (
            db.query(RealTimeData)
            .filter(
                RealTimeData.kpi== before_last_underscore,
                RealTimeData.name.in_(machine),
                RealTimeData.time.between(start_date, end_date),
                RealTimeData.operations.in_(operation)
            )
            .with_entities(RealTimeData.name ,RealTimeData.operations,RealTimeData.time,getattr(RealTimeData,after_last_underscore))
            .statement
        )
