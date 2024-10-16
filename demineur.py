# -*- coding: utf-8 -*-
"""
Created on Fri May 28 14:40:19 2021

@author: Thomas
"""

from typing import List, Tuple
import subprocess
from itertools import combinations
from crocomine_client import CrocomineClient
import numpy as np

# alias de types
Variable = int
Literal = int
Clause = List[Literal]
Model = List[Literal]
Clause_Base = List[Clause]
Grid = List[List[int]]
model = []
danger = []
old_pos = []
animals = []

def write_dimacs_file(dimacs: str, filename: str):
    with open(filename, "w", newline="") as cnf:
        cnf.write(dimacs)
        
def exec_gophersat(
    filename: str, cmd: str = "gophersat", arg:str = "", encoding: str = "utf8"
) -> Tuple[bool, List[int]]:
    if arg == "-count": #permet de connaître le nombre de solution possible
        result = subprocess.run(
            [cmd, arg, filename], capture_output=True, check=True, encoding=encoding
        )
        string = str(result.stdout)
        lines = string.splitlines()

        return int(lines[1])
    else:
        result = subprocess.run(
            [cmd, filename], capture_output=True, check=True, encoding=encoding
        )
        string = str(result.stdout)
        lines = string.splitlines()
        if lines[1] != "s SATISFIABLE":
            return False, []
        
        model = lines[2][2:].split(" ")
        return True, [int(x) for x in model]

#fonction pour traduire une case et une valeur vers une variable
def cell_to_variable(n:int, i:int, j:int, val:int):
    if val<0:
        return -((n*j + i) * 4 -val)
    else:
        return (n*j + i) * 4 +val
    
#fonction pour traduire une variable vers une case et une valeur
def variable_to_cell(n:int, val:int):
    if val<0:
        tmp = -val//4
        if val%4 == 0 and val != 0:
            val = 4
            tmp -= 1
        val = -1
        j = tmp//n
        i = tmp%n
    else:
        tmp = val//4
        if val%4 == 0 and val != 0:
            val = 4
            tmp -= 1
        else:
            val = val%4
        j = tmp//n
        i = tmp%n
        
    return [i, j, val]

def at_least_one(vars : List[int]):
    return vars
#permet de générer les combinaisons
def unique(vars : List[int]):
    result = [at_least_one(vars)]
    for i,j in combinations(vars,2):
        result.append([-i,-j])
    return result

# créer les contraintes d'un animal au plus par case
def create_animal_constraints(n:int, m:int):
    result = []
    for j in range(m):
        for i in range(n):
            l = []
            for val in range(3):
                l.append(cell_to_variable(n, i, j, val+2))
            result += unique(l)[1:]
    return result

# créer les contraintes pour associer le sol au type d'animal
def create_animal_terrain_constraints(n:int, m:int):
    result = []
    for j in range(m):
        for i in range(n):
            l1 = []
            l2 = []
            terrain = cell_to_variable(n, i, j, 1)
            l1.append(- terrain)
            l1.append(- (terrain+1))
            l2.append(terrain)
            l2.append(- (terrain+3))
            result += [l1]
            result += [l2]
    return result

# genere tout le programme au début
def generate_problem(n:int, m:int):
    global model
    model += create_animal_constraints(n, m)
    model += create_animal_terrain_constraints(n, m)
    return model

#génère la chaîne de caractères DIMACS
def clauses_to_dimacs(clauses : List[List[int]], nb_vars: int):
    result = 'p cnf ' + str(nb_vars) + ' ' + str(len(clauses)) +'\n'
    for i in range(len(clauses)):
        for j in range(len(clauses[i])):
            result += str(clauses[i][j]) + ' '
            if j == len(clauses[i])-1:
                result += '0\n'
    return result

#génère le fichier DIMACS
def generate_dimacs(n:int, m:int):
    write_dimacs_file(clauses_to_dimacs(generate_problem(n, m), n*m*4), 'problem.cnf')
    result = exec_gophersat('problem.cnf', 'gophersat-1.1.6.exe')
    return result

# permet de rajouter des infos au dimacs
def new_infos(n:int, m:int, info: List[int]):
    global model
    model += [info]
    write_dimacs_file(clauses_to_dimacs(model, n*m*4), 'problem.cnf')

# si il y a un animal proche permet de le notifier en dimacs    
def close_animal(n:int, m:int, infos: List[int]):
    result = []
    global old_pos
    danger = [infos["prox_count"]]
    for k in range(3):
        if infos["prox_count"][k] > 0:
            for i in range(3):
                for j in range(3):
                    if [infos["pos"][1] + j-1, infos["pos"][0] + i-1] != infos["pos"] and infos["pos"][1] + j-1 >= 0 and infos["pos"][0] + i-1 >= 0 and infos["pos"][1] + j-1 < m and infos["pos"][0] + i-1 < n:
                        if [infos["pos"][0] + i-1, infos["pos"][1] + j-1] not in old_pos:
                            danger += [[infos["pos"][0] + i-1, infos["pos"][1] + j-1]]
                            result += [cell_to_variable(n, infos["pos"][0] + i-1, infos["pos"][1] + j-1, (4-k))]
    new_infos(n, m, result)
    return danger       

#Compte le nombre de voisins
def close(n:int, m:int, infos: List[int]):
    result = 0
    for i in range(3):
        for j in range(3):
            if [infos[1] + j-1, infos[0] + i-1] != infos and infos[1] + j-1 >= 0 and infos[0] + i-1 >= 0 and infos[1] + j-1 < m and infos[0] + i-1 < n:
                result += 1
    return result

#decouvre une case et ajoute les infos dans le fichier dimacs
def discover(croco:CrocomineClient, n:int, m:int,  i:int, j:int, old_pos:List[int]):
    status, msg, infos = croco.discover(i, j)
    
    danger = []
    print(msg)
    if status == "OK":
        
        for k in range(len(infos)):
           infos[k]["pos"] = [infos[k]["pos"][1], infos[k]["pos"][0]]
           if "prox_count" in infos[k]:
                if infos[k]["field"] == 'sea': terrain = -1
                else: terrain = 1
                if [infos[k]["pos"]] not in old_pos: old_pos += [infos[k]["prox_count"], [infos[k]["pos"][0],infos[k]["pos"][1]]]
                var = cell_to_variable(n, infos[k]["pos"][0], infos[k]["pos"][1], terrain)
                new_infos(n, m, [var])
                if var >0: 
                    new_infos(n, m, [-(var+1)])
                    new_infos(n, m, [-(var+2)])
                    new_infos(n, m, [-(var+3)])
                else: 
                    new_infos(n, m, [var-1])
                    new_infos(n, m, [var-2])
                    new_infos(n, m, [var-3])
                danger += [close_animal(n, m, infos[k])]
           else:
                if infos[k]["field"] == 'sea': terrain = -1
                else: terrain = 1
                if [infos[k]["pos"]] not in old_pos:
                    var = cell_to_variable(n, infos[k]["pos"][0], infos[k]["pos"][1], terrain)
                    new_infos(n, m, [var])
            
    return status, msg, infos, danger

#fonction pour guess un animal
def guess(croco:CrocomineClient, n:int, m:int, info:List[int]):
    pos = variable_to_cell(n, info)
    if pos[2] == 2:
        status, msg, infos = croco.guess(pos[1], pos[0], "S")
        print(msg)
        if infos:
            infos[0]["pos"] = [infos[0]["pos"][1], infos[0]["pos"][0]]
    elif pos[2] == 3:
        status, msg, infos = croco.guess(pos[1], pos[0], "C")
        print(msg)
        if infos:
            infos[0]["pos"] = [infos[0]["pos"][1], infos[0]["pos"][0]]
    elif pos[2] == 4:
        status, msg, infos = croco.guess(pos[1], pos[0], "T")
        print(msg)
        if infos:
            infos[0]["pos"] = [infos[0]["pos"][1], infos[0]["pos"][0]]
    else: print("Erreur il n'y a pas d'animal")
    return status, msg, infos

#fonction pour tester avec gophersat si il y a un animal
def test_guess(n:int, m:int, val: int):
    global model
    model_test = model.copy()
    model_test.append([-val])
    write_dimacs_file(clauses_to_dimacs(model_test, n*m*4), 'test.cnf')
    result = exec_gophersat('test.cnf', 'gophersat-1.1.6.exe')
    return result
    
# l'IA qui joue au démineur
def joueur(croco:CrocomineClient, status:str, msg:str, grid_infos):
    print(msg)
    m = grid_infos["m"]
    n = grid_infos["n"]
    pos = grid_infos["start"]
    danger_proba = []
    danger_prox_count = []
    
    global danger 
    danger = []
    global old_pos 
    old_pos = []
    global animals 
    animals = []
    global model
    model = []
    generate_dimacs(n, m)

    #Tant qu'il n'y a pas d'erreur on continue
    while status == 'OK':
        #si la position n'est pas susceptible d'être un animal on le découvre
        if pos != danger_proba:
            danger_proba = []
            status, msg, infos, inconnu = discover(croco, n, m, pos[0], pos[1], old_pos)
            if status != 'OK': break
            #On ajoute les cases susceptible d'être un animal dans la liste danger
            for k in inconnu:
                if len(k)>1: danger += [k]
                
        list_proba = np.zeros((m, n))
        list_proba_prox_count = []
        
        #On effectue les probas pour chaque cases susceptible d'être un animal
        for k in danger:
            for l in range(len(k)-1):
                if k[l+1] not in old_pos:
                    list_proba[k[l+1][1],k[l+1][0]] += 1/close(n, m, k[l+1])
                    list_proba_prox_count += [[k[0], [k[l+1][0],k[l+1][1]]]]
                    
       #Si la case a déjà était découvert, on met -1 pour l'ignorer
        for i in range(n):
            for j in range(m):
                if [i, j] in old_pos:
                    list_proba[j, i] = -1
        cpt = 1000
        cpt2 = 0
    
        for i in range(n):
            for j in range(m):
                if list_proba[j][i]>-1:
                    #Si la case a une proba >=0 on prend la plus petite valeur pour la découvrir après
                    if list_proba[j][i] < cpt:
                        cpt = list_proba[j][i]
                        pos = [j, i]
                 #sinon on prend le max pour tenter de guess       
                if list_proba[j][i]>0:
                    if list_proba[j][i] > cpt2: 
                        cpt2 = list_proba[j][i]
                        danger_proba = [i, j]
                        for k in range(len(list_proba_prox_count)):
                            if danger_proba == list_proba_prox_count[k][1]:
                                danger_prox_count = list_proba_prox_count[k][0]
        print(list_proba) 
        cond = True
        if danger_proba == [] or cpt == cpt2:
            cond = False
            
        if danger_prox_count[0]>0:
            ani_type = 4
        elif danger_prox_count[1]>0:
            ani_type = 2
        elif danger_prox_count[2]>0:
            ani_type = 3
        
        #si il y a une grande chose que ce soit un animal on essaye de guess
        if cond == True:
            cond = False
            test = cell_to_variable(n, danger_proba[0], danger_proba[1], ani_type)
            result_test = test_guess(n, m, test)
            #si le test est faux, alors on est sur qu'il y a un animal
            if result_test[0] == False:
                        for k in danger:
                            if danger_proba in k:
                                if ani_type == 2 and k[0][1] > 0 :
                                    k[0][1] -= 1
                                elif ani_type == 3  and k[0][2] > 0:
                                    k[0][2] -= 1
                                elif ani_type == 4  and k[0][0] > 0:
                                    k[0][0] -= 1
                                    
                        status, msg, infos = guess(croco, n, m, test)
                        old_pos += [[0,0,0], [danger_proba[0], danger_proba[1]]]
                        if status != 'OK': break
    
# création du jeu
def main():
    # il faut lancer le serveur au début avec .\serveur\bin\crocomine-lite-beta3.exe ":8000" .\serveur\cartes\
    #server = "http://localhost:8000"
    server = "http://croco.lagrue.ninja:80"
    group = "Groupe 38"
    members = "Thomas Leymonerie et Youssef Ben Khelil"
    password = "ThomasYoussef"
    croco = CrocomineClient(server, group, members, password)
    status, msg, grid_infos = croco.new_grid()
    
    joueur(croco, status, msg, grid_infos)
    
    #chaque carte est joué automatiquement au fur et à mesure
    while status == 'OK':
        status, msg, grid_infos = croco.new_grid()
        if status != 'OK':
            break
        print("")
        print("------------------------------")
        print("/////////// NEW GRID \\\\\\\\\\\ ")
        print("------------------------------")
        print("")
        joueur(croco, status, msg, grid_infos)

    print("")
    print("------------------------------")
    print("/////////// THE END \\\\\\\\\\\ ")
    print("------------------------------")
    print("")
        
if __name__ == "__main__":
    main()
   
    
