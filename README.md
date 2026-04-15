# Flappy Bird — NEAT AI

> Un agent IA qui apprend à jouer à Flappy Bird grâce à un algorithme génétique (NEAT) codé **from scratch** en Python.

![Demo](assets/demo.gif)

---

## Aperçu

Ce projet implémente un système d'**intelligence artificielle évolutive** appliqué au jeu Flappy Bird. L'IA ne reçoit aucune règle précodée : elle apprend uniquement par l'expérience, génération après génération, en faisant évoluer un réseau de neurones maison.

L'algorithme s'inspire du **NEAT** *(NeuroEvolution of Augmenting Topologies)* — sélection naturelle appliquée aux réseaux de neurones.

---

## Fonctionnement de l'IA

```
5 entrées → 8 neurones cachés → 1 sortie (sauter / ne pas sauter)
```

**Entrées du réseau :**
| Entrée | Description |
|--------|-------------|
| `y_norm` | Position verticale de l'oiseau (normalisée) |
| `vy_norm` | Vitesse verticale |
| `dist_norm` | Distance au prochain tuyau |
| `trou_norm` | Hauteur du centre du trou |
| `diff_norm` | Différence entre l'oiseau et le centre du trou |

**Fonction d'activation :** `tanh`

**Fitness :** `ticks_survie + score × 1000`

**Algorithme génétique :**
- Population de 50 oiseaux par génération
- Élitisme (les 2 meilleurs passent intacts)
- Croisement uniforme entre les parents sélectionnés
- Mutation gaussienne des poids (`σ = 0.2`)
- Taux de mutation augmenté automatiquement en cas de stagnation

---

## Démo

Après quelques générations, l'IA passe des tuyaux indéfiniment. Le panneau en temps réel affiche la génération courante, le nombre d'oiseaux vivants, l'évolution du score, et un graphique des performances.

---

## Structure du projet

```
flappybird/
├── assets/              # Images du jeu (oiseaux, tuyaux, fond, chiffres…)
├── code/
│   ├── flappy.py        # Version manuelle (jouable au clavier)
│   ├── flappy_ai.py     # Version IA avec NEAT
│   └── flappy_save.json # Sauvegarde automatique de la meilleure IA
└── README.md
```

---

## Installation & Lancement

**Prérequis :** Python 3.8+ et `pygame`

```bash
pip install pygame
```

**Lancer la version IA :**
```bash
python code/flappy_ai.py
```

**Lancer la version manuelle :**
```bash
python code/flappy.py
```

---

## Contrôles (version IA)

| Touche | Action |
|--------|--------|
| `ESPACE` | Pause / Reprendre |
| `↑` / `↓` | Augmenter / Diminuer la vitesse de simulation |
| `R` | Tuer tous les oiseaux (forcer une nouvelle génération) |

La sauvegarde est automatique à chaque fin de génération.

---

## Stack technique

- **Python 3** — langage principal
- **Pygame** — moteur graphique et gestion des événements
- **Réseau de neurones custom** — implémenté from scratch (pas de TensorFlow/PyTorch)
- **Algorithme génétique custom** — sélection, croisement, mutation, élitisme

---

## Auteur

**Isidore Zongo**  
