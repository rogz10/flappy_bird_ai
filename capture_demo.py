"""
Script de capture GIF pour la démo portfolio.
Lance la simulation avec le meilleur cerveau sauvegardé et enregistre assets/demo.gif.
"""

import pygame
import random
import sys
import os
import math
import json
import numpy as np
from PIL import Image

# ── Chemins ──────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
CODE_DIR    = os.path.join(BASE_DIR, "code")
SAVE_FILE   = os.path.join(CODE_DIR, "flappy_save.json")
OUTPUT_GIF  = os.path.join(ASSETS_DIR, "demo.gif")

# ── Constantes ────────────────────────────────────────────────────────────────
LARGEUR           = 400
HAUTEUR           = 600
FPS               = 60
GRAVITE           = 0.5
FORCE_SAUT        = -9
VITESSE_JEU       = 4
ESPACE_TUYAUX     = 150
INTERVALLE_TUYAUX = 200
HAUTEUR_SOL       = HAUTEUR - 100

CAPTURE_DURATION_S = 12    # secondes à capturer
CAPTURE_EVERY_N    = 3     # capturer 1 frame sur N (→ ~20 fps dans le GIF)
GIF_SCALE          = 0.75  # facteur de réduction du GIF

# ── Pygame ────────────────────────────────────────────────────────────────────
pygame.init()
ecran      = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Flappy Bird — Capture démo")
horloge    = pygame.time.Clock()
font_small = pygame.font.SysFont("Consolas", 14)
font_med   = pygame.font.SysFont("Consolas", 18, bold=True)
BLANC      = (255, 255, 255)
NOIR       = (0, 0, 0)
CYAN       = (0, 200, 220)
JAUNE      = (255, 220, 50)
ORANGE     = (255, 140, 0)
ROUGE      = (220, 60, 60)
VERT       = (80, 200, 80)
GRIS       = (100, 100, 100)
GRIS_CLAIR = (200, 200, 200)

# ── Images ────────────────────────────────────────────────────────────────────
def charger_image(nom, taille=None):
    img = pygame.image.load(os.path.join(ASSETS_DIR, nom)).convert_alpha()
    if taille:
        img = pygame.transform.scale(img, taille)
    return img

img_fond       = charger_image("background-day.png", (LARGEUR, HAUTEUR))
img_sol        = charger_image("base.png", (LARGEUR, 100))
img_oiseau     = [
    charger_image("yellowbird-downflap.png", (45, 32)),
    charger_image("yellowbird-midflap.png",  (45, 32)),
    charger_image("yellowbird-upflap.png",   (45, 32)),
]
img_tuyau_bas  = charger_image("pipe-green.png", (65, 400))
img_tuyau_haut = pygame.transform.flip(img_tuyau_bas, False, True)
img_chiffres   = [charger_image(f"{i}.png", (30, 44)) for i in range(10)]

# ── Réseau de neurones ────────────────────────────────────────────────────────
class Neurone:
    def __init__(self, poids, biais):
        self.poids = poids
        self.biais = biais

    def activer(self, entrees):
        return math.tanh(sum(p * e for p, e in zip(self.poids, entrees)) + self.biais)


class ReseauNeurones:
    def __init__(self, data):
        self.couche_cachee = [Neurone(n["poids"], n["biais"]) for n in data["couche_cachee"]]
        self.sortie        = Neurone(data["sortie"]["poids"], data["sortie"]["biais"])

    def predire(self, entrees):
        valeurs = [n.activer(entrees) for n in self.couche_cachee]
        return self.sortie.activer(valeurs)


# ── Entités ───────────────────────────────────────────────────────────────────
class Oiseau:
    def __init__(self, cerveau):
        self.x             = 80
        self.y             = float(HAUTEUR // 2)
        self.vitesse_y     = 0.0
        self.frame         = 0
        self.compteur_anim = 0
        self.vivant        = True
        self.score         = 0
        self.cerveau       = cerveau

    def obtenir_entrees(self, tuyaux):
        prochain = next((t for t in tuyaux if t.x + 65 > self.x - 10), None)
        y_norm   = self.y / HAUTEUR_SOL
        vy_norm  = self.vitesse_y / 15.0
        if prochain:
            dist_norm = (prochain.x - self.x) / LARGEUR
            trou_norm = prochain.centre_trou / HAUTEUR_SOL
            diff_norm = (self.y - prochain.centre_trou) / HAUTEUR_SOL
        else:
            dist_norm, trou_norm, diff_norm = 1.0, 0.5, 0.0
        return [y_norm, vy_norm, dist_norm, trou_norm, diff_norm]

    def penser(self, tuyaux):
        if self.cerveau.predire(self.obtenir_entrees(tuyaux)) > 0:
            self.vitesse_y = FORCE_SAUT

    def mise_a_jour(self):
        self.vitesse_y     += GRAVITE
        self.y             += self.vitesse_y
        self.compteur_anim += 1
        if self.compteur_anim >= 5:
            self.compteur_anim = 0
            self.frame = (self.frame + 1) % 3

    def obtenir_rect(self):
        rect = img_oiseau[self.frame].get_rect(center=(self.x, int(self.y)))
        return rect.inflate(-6, -6)

    def dessiner(self, surface):
        img    = img_oiseau[self.frame]
        angle  = max(-90, min(-self.vitesse_y * 3, 25))
        rotated = pygame.transform.rotate(img, angle)
        surface.blit(rotated, rotated.get_rect(center=(self.x, int(self.y))))


class Tuyau:
    def __init__(self, x):
        self.x           = x
        self.centre_trou = random.randint(130, HAUTEUR_SOL - 130)
        self.deja_passe  = False

    def mise_a_jour(self):
        self.x -= VITESSE_JEU

    def est_hors_ecran(self):
        return self.x + 65 < 0

    def obtenir_rects(self):
        y_haut = self.centre_trou - ESPACE_TUYAUX // 2 - 400
        y_bas  = self.centre_trou + ESPACE_TUYAUX // 2
        return (pygame.Rect(self.x, y_haut, 65, 400),
                pygame.Rect(self.x, y_bas,  65, 400))

    def collision(self, rect):
        return any(rect.colliderect(r) for r in self.obtenir_rects())

    def dessiner(self, surface):
        y_haut = self.centre_trou - ESPACE_TUYAUX // 2 - 400
        y_bas  = self.centre_trou + ESPACE_TUYAUX // 2
        surface.blit(img_tuyau_haut, (self.x, y_haut))
        surface.blit(img_tuyau_bas,  (self.x, y_bas))


class Sol:
    def __init__(self):
        self.x1 = 0
        self.x2 = LARGEUR

    def mise_a_jour(self):
        self.x1 -= VITESSE_JEU
        self.x2 -= VITESSE_JEU
        if self.x1 + LARGEUR <= 0:
            self.x1 = self.x2 + LARGEUR
        if self.x2 + LARGEUR <= 0:
            self.x2 = self.x1 + LARGEUR

    def dessiner(self, surface):
        surface.blit(img_sol, (self.x1, HAUTEUR_SOL))
        surface.blit(img_sol, (self.x2, HAUTEUR_SOL))


def afficher_score(surface, score):
    texte = str(score)
    x     = (LARGEUR - len(texte) * 30) // 2
    for i, c in enumerate(texte):
        surface.blit(img_chiffres[int(c)], (x + i * 30, 50))


def dessiner_hud(surface, score, meilleur_score):
    panel = pygame.Surface((160, 55), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 140))
    surface.blit(panel, (5, 5))
    surface.blit(font_med.render(f"SCORE  {score}", True, JAUNE), (12, 10))
    surface.blit(font_med.render(f"BEST   {meilleur_score}", True, ORANGE), (12, 32))


# ── Capture ───────────────────────────────────────────────────────────────────
def surface_to_pil(surface, scale):
    raw   = pygame.surfarray.array3d(surface)  # (W, H, 3)
    raw   = raw.transpose(1, 0, 2)             # → (H, W, 3)
    img   = Image.fromarray(raw, "RGB")
    if scale != 1.0:
        new_w = int(img.width  * scale)
        new_h = int(img.height * scale)
        img   = img.resize((new_w, new_h), Image.LANCZOS)
    return img


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Chargement du meilleur cerveau
    if not os.path.exists(SAVE_FILE):
        print("[ERREUR] Aucune sauvegarde trouvée. Lance d'abord flappy_ai.py.")
        pygame.quit()
        sys.exit(1)

    with open(SAVE_FILE) as f:
        data = json.load(f)

    cerveau        = ReseauNeurones(data["meilleur_cerveau"])
    meilleur_score = data.get("meilleur_score", 0)

    oiseau  = Oiseau(cerveau)
    tuyaux  = []
    sol     = Sol()
    score   = 0
    frames  = []

    total_ticks   = CAPTURE_DURATION_S * FPS
    tick          = 0
    frame_counter = 0

    print(f"[INFO] Capture de {CAPTURE_DURATION_S}s → {OUTPUT_GIF}")
    print(f"[INFO] Meilleur score chargé : {meilleur_score}")

    while tick < total_ticks:
        horloge.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # --- Logique ---
        if not tuyaux or tuyaux[-1].x < LARGEUR - INTERVALLE_TUYAUX:
            tuyaux.append(Tuyau(LARGEUR))
        for t in tuyaux:
            t.mise_a_jour()
        tuyaux = [t for t in tuyaux if not t.est_hors_ecran()]
        sol.mise_a_jour()

        if oiseau.vivant:
            oiseau.penser(tuyaux)
            oiseau.mise_a_jour()
            rect = oiseau.obtenir_rect()
            if oiseau.y >= HAUTEUR_SOL - 15 or oiseau.y <= 0:
                oiseau.vivant = False
            for t in tuyaux:
                if t.collision(rect):
                    oiseau.vivant = False
            for t in tuyaux:
                if not t.deja_passe and t.x + 65 < oiseau.x:
                    oiseau.score  += 1
                    t.deja_passe   = True
            score = oiseau.score

        if not oiseau.vivant:
            # relancer l'oiseau pour garder la démo en mouvement
            oiseau        = Oiseau(cerveau)
            tuyaux        = []
            score         = 0

        # --- Dessin ---
        ecran.blit(img_fond, (0, 0))
        for t in tuyaux:
            t.dessiner(ecran)
        sol.dessiner(ecran)

        # ligne de guidage vers le tuyau
        if tuyaux:
            prochain = next((t for t in tuyaux if t.x + 65 > oiseau.x - 10), None)
            if prochain:
                pygame.draw.line(ecran, (255, 255, 0),
                                 (oiseau.x, int(oiseau.y)),
                                 (prochain.x, prochain.centre_trou), 1)

        oiseau.dessiner(ecran)
        afficher_score(ecran, score)
        dessiner_hud(ecran, score, meilleur_score)
        pygame.display.flip()

        # --- Capture ---
        if frame_counter % CAPTURE_EVERY_N == 0:
            frames.append(surface_to_pil(ecran, GIF_SCALE))

        frame_counter += 1
        tick          += 1

        if tick % FPS == 0:
            print(f"  {tick // FPS}s / {CAPTURE_DURATION_S}s  ({len(frames)} frames)")

    pygame.quit()

    # ── Sauvegarde GIF ────────────────────────────────────────────────────────
    print(f"[INFO] Sauvegarde du GIF ({len(frames)} frames)…")
    delay_ms = int(1000 / (FPS / CAPTURE_EVERY_N))  # durée par frame en ms
    frames[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=delay_ms,
        loop=0,
        optimize=True,
    )
    size_kb = os.path.getsize(OUTPUT_GIF) // 1024
    print(f"[OK] GIF sauvegardé : {OUTPUT_GIF}  ({size_kb} Ko)")


if __name__ == "__main__":
    main()
