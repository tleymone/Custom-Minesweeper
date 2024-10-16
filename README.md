# Projet démineur (Groupe 38)

UTC project made in 2021.

## Spécificité

Le but du cet IA est de trouver les cases vides et les animaux de façon certaine.
Pour cela, on créé une matrice de probabilités pour chaque case. La probabilité est calculée par rapport au nombre de cases adjacentes qui ont un prox_count > 0 sur le nombre de voisins que possède la case.
Pour les cases déjà visitée la probabilité est à -1.
La case avec la plus grande chance d'être un animal sera testée avant d'effectuer le guess.
Et la case avec le moins de chance d'être un animal sera prise pour découvrir la case.
Et on recommence jusqu'à la fin de la carte

## Problèmes

Il y a 2 problèmes principaux.
Le premier concerne les probabilités, puisqu'il y a toujours une chance que la case avec la probabilité la plus haute d'avoir un animal est une case sans animal.
Le deuxième vient du fichier DIMACS, à partir d'un certain moment le fichier devient insatisfiable sans raison, donc un guess est effectué alors qu'il est faux.

Pour résoudre le premier, on pourrait faire en sorte que le programme cherche plus les cases vides que les animaux au début du programme.
Pour le deuxième, il faut modifier les fonctions de créeations des règles, guess et discover pour être sur qu'il n'y ai pas d'erreur de code dans ces fonctions.
