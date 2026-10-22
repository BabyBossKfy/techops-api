# Procédure : perte de liaison réseau

Document fictif rédigé pour la démonstration du projet.

## Symptômes

Les applications métiers ne répondent plus, la liaison réseau entre deux sites est coupée ou la latence devient très élevée.

## Diagnostic

1. Identifier le périmètre touché : un poste, un service ou l'ensemble du site.
2. Vérifier l'état des commutateurs et des routeurs dans l'outil de supervision réseau.
3. Lancer un ping vers la passerelle, puis vers le site distant.

## Escalade

Si la liaison principale reste coupée plus de dix minutes, basculer sur la liaison de secours et prévenir l'opérateur télécom. Ouvrir un incident de sévérité moyenne ou critique selon le nombre d'utilisateurs touchés.
