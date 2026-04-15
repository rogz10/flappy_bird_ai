import pygame
import random
import sys
import os


# ============================================================
#  INITIALISATION DE PYGAME
# ============================================================
pygame.init()


# ============================================================
#  CONSTANTES DU JEU
# ============================================================
LARGEUR = 400
HAUTEUR = 600
FPS = 30

GRAVITE = 0.5
FORCE_SAUT = -9
VITESSE_JEU = 4
ESPACE_TUYAUX = 150
INTERVALLE_TUYAUX = 200

HAUTEUR_SOL = HAUTEUR - 100

ETAT_MENU = 0
ETAT_JEU = 1
ETAT_GAME_OVER = 2


# ============================================================
#  FENÊTRE ET HORLOGE
# ============================================================
ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Flappy Bird")
horloge = pygame.time.Clock()


# ============================================================
#  CHARGEMENT DES IMAGES
# ============================================================
DOSSIER_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")


def charger_image(nom, taille=None):
    """Charge une image depuis le dossier assets et la redimensionne si besoin."""
    chemin = os.path.join(DOSSIER_ASSETS, nom)
    image = pygame.image.load(chemin).convert_alpha()
    if taille:
        image = pygame.transform.scale(image, taille)
    print(f"Image chargée : {chemin}")
    print(f"Taille : {image.get_width()}x{image.get_height()}")
    print(f"Type : {type(image)}")
    #print(f"Format : {image.get_format()}")
    #print(f"Mode : {image.get_mode()}")
    #print(f"Couleurs : {image.get_colorspace()}")
    print(f"Alpha : {image.get_alpha()}")
    #print(f"Surface : {image.get_surface()}")
    #print(f"Rect : {image.get_rect()}")
    return image


img_fond = charger_image("background-day.png", (LARGEUR, HAUTEUR))
img_sol = charger_image("base.png", (LARGEUR, 100))

img_oiseau = [
    charger_image("yellowbird-downflap.png", (45, 32)),
    charger_image("yellowbird-midflap.png", (45, 32)),
    charger_image("yellowbird-upflap.png", (45, 32)),
]

img_tuyau_bas = charger_image("pipe-green.png", (65, 400))
img_tuyau_haut = pygame.transform.flip(img_tuyau_bas, False, True)

img_chiffres = [charger_image(f"{i}.png", (30, 44)) for i in range(10)]

img_message = charger_image("message.png", (230, 320))
img_game_over = charger_image("gameover.png", (250, 60))


# ============================================================
#  CLASSE OISEAU
# ============================================================
class Oiseau:
    def __init__(self):
        self.x = 80
        self.y = HAUTEUR // 2
        self.vitesse_y = 0
        self.frame = 0
        self.compteur_anim = 0

    def sauter(self):
        self.vitesse_y = FORCE_SAUT

    def mise_a_jour(self):
        self.vitesse_y += GRAVITE
        self.y += self.vitesse_y

        self.compteur_anim += 1
        if self.compteur_anim >= 5:
            self.compteur_anim = 0
            self.frame = (self.frame + 1) % 3

    def obtenir_rect(self):
        image = img_oiseau[self.frame]
        rect = image.get_rect(center=(self.x, int(self.y)))
        return rect.inflate(-6, -6)

    def dessiner(self, surface):
        image = img_oiseau[self.frame]
        angle = -self.vitesse_y * 3
        angle = max(-90, min(angle, 25))
        image_tournee = pygame.transform.rotate(image, angle)
        rect = image_tournee.get_rect(center=(self.x, int(self.y)))
        surface.blit(image_tournee, rect)


# ============================================================
#  CLASSE TUYAU
# ============================================================
class Tuyau:
    LARGEUR_IMG = 65
    HAUTEUR_IMG = 400

    def __init__(self, x):
        self.x = x
        self.centre_trou = random.randint(130, HAUTEUR_SOL - 130)
        self.deja_passe = False

    def mise_a_jour(self):
        self.x -= VITESSE_JEU

    def est_hors_ecran(self):
        return self.x + self.LARGEUR_IMG < 0

    def obtenir_rects(self):
        y_haut = self.centre_trou - ESPACE_TUYAUX // 2 - self.HAUTEUR_IMG
        y_bas = self.centre_trou + ESPACE_TUYAUX // 2

        rect_haut = pygame.Rect(self.x, y_haut, self.LARGEUR_IMG, self.HAUTEUR_IMG)
        rect_bas = pygame.Rect(self.x, y_bas, self.LARGEUR_IMG, self.HAUTEUR_IMG)
        return rect_haut, rect_bas

    def collision(self, rect_oiseau):
        rect_haut, rect_bas = self.obtenir_rects()
        return rect_oiseau.colliderect(rect_haut) or rect_oiseau.colliderect(rect_bas)

    def dessiner(self, surface):
        y_haut = self.centre_trou - ESPACE_TUYAUX // 2 - self.HAUTEUR_IMG
        y_bas = self.centre_trou + ESPACE_TUYAUX // 2
        surface.blit(img_tuyau_haut, (self.x, y_haut))
        surface.blit(img_tuyau_bas, (self.x, y_bas))


# ============================================================
#  CLASSE SOL (défilement infini)
# ============================================================
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


# ============================================================
#  AFFICHAGE DU SCORE AVEC LES IMAGES DE CHIFFRES
# ============================================================
def afficher_score(surface, score, y=50):
    texte = str(score)
    largeur_totale = len(texte) * 30
    x_depart = (LARGEUR - largeur_totale) // 2
    for i, caractere in enumerate(texte):
        chiffre = int(caractere)
        surface.blit(img_chiffres[chiffre], (x_depart + i * 30, y))


# ============================================================
#  BOUCLE PRINCIPALE
# ============================================================
def main():
    etat = ETAT_MENU
    oiseau = Oiseau()
    tuyaux = []
    sol = Sol()
    score = 0
    meilleur_score = 0
    font_ui = pygame.font.SysFont("Arial", 20)

    while True:
        horloge.tick(FPS)

        # ---- ÉVÉNEMENTS ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            action = (
                (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)
                or event.type == pygame.MOUSEBUTTONDOWN
            )

            if action:
                if etat == ETAT_MENU:
                    etat = ETAT_JEU
                    oiseau.sauter()
                elif etat == ETAT_JEU:
                    oiseau.sauter()
                elif etat == ETAT_GAME_OVER:
                    etat = ETAT_MENU
                    oiseau = Oiseau()
                    tuyaux = []
                    score = 0

        # ---- MISE À JOUR ----
        if etat == ETAT_JEU:
            oiseau.mise_a_jour()
            sol.mise_a_jour()

            if len(tuyaux) == 0 or tuyaux[-1].x < LARGEUR - INTERVALLE_TUYAUX:
                tuyaux.append(Tuyau(LARGEUR))

            for t in tuyaux:
                t.mise_a_jour()

            tuyaux = [t for t in tuyaux if not t.est_hors_ecran()]

            rect_oiseau = oiseau.obtenir_rect()
            for t in tuyaux:
                if t.collision(rect_oiseau):
                    etat = ETAT_GAME_OVER
                    meilleur_score = max(meilleur_score, score)

            if oiseau.y >= HAUTEUR_SOL - 16 or oiseau.y <= 0:
                etat = ETAT_GAME_OVER
                meilleur_score = max(meilleur_score, score)

            for t in tuyaux:
                if not t.deja_passe and t.x + Tuyau.LARGEUR_IMG < oiseau.x:
                    score += 1
                    t.deja_passe = True

        elif etat == ETAT_MENU:
            sol.mise_a_jour()
            oiseau.compteur_anim += 1
            if oiseau.compteur_anim >= 5:
                oiseau.compteur_anim = 0
                oiseau.frame = (oiseau.frame + 1) % 3

        # ---- DESSIN ----
        ecran.blit(img_fond, (0, 0))

        for t in tuyaux:
            t.dessiner(ecran)

        sol.dessiner(ecran)
        oiseau.dessiner(ecran)

        if etat == ETAT_JEU:
            afficher_score(ecran, score)

        if etat == ETAT_MENU:
            ecran.blit(img_message, ((LARGEUR - 230) // 2, (HAUTEUR - 320) // 2 - 30))

        if etat == ETAT_GAME_OVER:
            ecran.blit(img_game_over, ((LARGEUR - 250) // 2, 150))
            afficher_score(ecran, score, y=230)

            txt_best = font_ui.render(f"Meilleur : {meilleur_score}", True, (255, 255, 255))
            ecran.blit(txt_best, txt_best.get_rect(center=(LARGEUR // 2, 290)))

            txt_rejouer = font_ui.render("ESPACE pour rejouer", True, (255, 255, 255))
            ecran.blit(txt_rejouer, txt_rejouer.get_rect(center=(LARGEUR // 2, 330)))

        pygame.display.flip()


if __name__ == "__main__":
    main()
