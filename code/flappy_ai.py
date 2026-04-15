import pygame
import random
import sys
import os
import math
import json

pygame.init()

# initialisation de pygame
pygame.init()

# initialisation des constantes
LARGEUR = 400
HAUTEUR = 600
FPS = 60

GRAVITE = 0.5
FORCE_SAUT = -9
VITESSE_JEU = 4
ESPACE_TUYAUX = 150
INTERVALLE_TUYAUX = 200
HAUTEUR_SOL = HAUTEUR - 100

# initialisation de neat
TAILLE_POPULATION = 50
TAUX_MUTATION = 0.1
TAUX_CROISEMENT = 0.75

# initialisation des couleurs ui
BLANC      = (255, 255, 255)
NOIR       = (0,   0,   0  )
CYAN       = (0,   200, 220)
JAUNE      = (255, 220, 50 )
ORANGE     = (255, 140, 0  )
ROUGE      = (220, 60,  60 )
VERT       = (80,  200, 80 )
GRIS       = (100, 100, 100)
GRIS_CLAIR = (200, 200, 200)

ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Flappy Bird — NEAT AI")
horloge = pygame.time.Clock()
font_small = pygame.font.SysFont("Consolas", 14)
font_med   = pygame.font.SysFont("Consolas", 18, bold=True)
font_large = pygame.font.SysFont("Consolas", 26, bold=True)

#  chargement des images 
DOSSIER_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
# fonction de chargement des images
def charger_image(nom, taille=None):
    chemin = os.path.join(DOSSIER_ASSETS, nom)
    image = pygame.image.load(chemin).convert_alpha()
    if taille:
        image = pygame.transform.scale(image, taille)
    return image

img_fond     = charger_image("background-day.png", (LARGEUR, HAUTEUR))
img_sol      = charger_image("base.png", (LARGEUR, 100))
img_oiseau   = [
    charger_image("yellowbird-downflap.png", (45, 32)),
    charger_image("yellowbird-midflap.png",  (45, 32)),
    charger_image("yellowbird-upflap.png",   (45, 32)),
]
img_tuyau_bas = charger_image("pipe-green.png", (65, 400))
img_tuyau_haut = pygame.transform.flip(img_tuyau_bas, False, True)
img_chiffres  = [charger_image(f"{i}.png", (30, 44)) for i in range(10)]
img_game_over = charger_image("gameover.png", (250, 60))


#  reseau de neurones
class Neurone:
    """neurone avec un nombre d'entrées et des poids et un biais, 
    une fonction d'activation et une fonction de copie, et une fonction de mutation
    """
    def __init__(self, nb_entrees):
        self.poids = [random.uniform(-1, 1) for _ in range(nb_entrees)] # poids aléatoires entre -1 et 1
        self.biais  = random.uniform(-1, 1) # biais aléatoire entre -1 et 1

    def activer(self, entrees):
        somme = sum(p * e for p, e in zip(self.poids, entrees)) + self.biais # somme des produits des poids et des entrées + le biais
        return math.tanh(somme) # fonction d'activation tangente hyperbolique

    def copier(self):
        n = Neurone(len(self.poids)) # création d'un nouveau neurone avec le même nombre d'entrées
        n.poids = self.poids[:] 
        n.biais  = self.biais
        return n

    def muter(self, taux):
        for i in range(len(self.poids)):
            if random.random() < taux:
                if random.random() < 0.1:
                    self.poids[i] = random.uniform(-1, 1)
                else:
                    self.poids[i] = max(-2, min(2, self.poids[i] + random.gauss(0, 0.2)))
        if random.random() < taux:
            self.biais += random.gauss(0, 0.2)


class ReseauNeurones:
    """reseau de neurones avec une couche cachee et une sortie, 
    une fonction de prediction, une fonction de copie, une fonction de mutation, 
    et une fonction de croisement pour creer un enfant a partir de deux parents pour la nouvelle generation
    5 entrées, 8 neurones cachés, 1 sortie
    """
    def __init__(self):
        self.couche_cachee = [Neurone(5) for _ in range(8)]
        self.sortie        = Neurone(8)

    def predire(self, entrees):
        valeurs = [n.activer(entrees) for n in self.couche_cachee]
        return self.sortie.activer(valeurs)

    def copier(self):
        r = ReseauNeurones.__new__(ReseauNeurones)
        r.couche_cachee = [n.copier() for n in self.couche_cachee]
        r.sortie        = self.sortie.copier()
        return r

    def muter(self, taux=TAUX_MUTATION):
        for n in self.couche_cachee:
            n.muter(taux)
        self.sortie.muter(taux)

    @staticmethod
    def croisement(p1, p2):
        enfant = ReseauNeurones()
        for i, (n1, n2) in enumerate(zip(p1.couche_cachee, p2.couche_cachee)):
            for j in range(len(n1.poids)):
                enfant.couche_cachee[i].poids[j] = n1.poids[j] if random.random() < 0.5 else n2.poids[j]
            enfant.couche_cachee[i].biais = n1.biais if random.random() < 0.5 else n2.biais
        for j in range(len(p1.sortie.poids)):
            enfant.sortie.poids[j] = p1.sortie.poids[j] if random.random() < 0.5 else p2.sortie.poids[j]
        enfant.sortie.biais = p1.sortie.biais if random.random() < 0.5 else p2.sortie.biais
        return enfant

    def vers_dict(self):
        return {
            "couche_cachee": [{"poids": n.poids, "biais": n.biais} for n in self.couche_cachee],
            "sortie":         {"poids": self.sortie.poids, "biais": self.sortie.biais}
        }

    @staticmethod
    def depuis_dict(data):
        r = ReseauNeurones.__new__(ReseauNeurones)
        r.couche_cachee = []
        for nd in data["couche_cachee"]:
            n = Neurone.__new__(Neurone)
            n.poids = nd["poids"]; n.biais = nd["biais"]
            r.couche_cachee.append(n)
        n = Neurone.__new__(Neurone)
        n.poids = data["sortie"]["poids"]; n.biais = data["sortie"]["biais"]
        r.sortie = n
        return r



#  sauvegarde / chargement
FICHIER_SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flappy_save.json")

def sauvegarder(neat):
    if neat.meilleur_cerveau is None:
        return
    data = {
        "generation":       neat.generation,
        "meilleur_score":   neat.meilleur_score,
        "meilleur_fitness": neat.meilleur_fitness,
        "historique_scores":neat.historique_scores,
        "meilleur_cerveau": neat.meilleur_cerveau.vers_dict()
    }
    with open(FICHIER_SAVE, "w") as f:
        json.dump(data, f)
    print(f"[SAVE] Gen {neat.generation} — score {neat.meilleur_score}")

def charger(neat):
    if not os.path.exists(FICHIER_SAVE):
        print("[LOAD] Aucune sauvegarde, départ from scratch.")
        return False
    with open(FICHIER_SAVE, "r") as f:
        data = json.load(f)
    neat.generation        = data["generation"]
    neat.meilleur_score    = data["meilleur_score"]
    neat.meilleur_fitness  = data["meilleur_fitness"]
    neat.historique_scores = data.get("historique_scores", [])
    neat.meilleur_cerveau  = ReseauNeurones.depuis_dict(data["meilleur_cerveau"])
    for i, o in enumerate(neat.population):
        cerveau = neat.meilleur_cerveau.copier()
        if i >= 2:
            cerveau.muter(TAUX_MUTATION * 2)
        o.cerveau = cerveau
    print(f"[LOAD] Reprise gen {neat.generation} — best score {neat.meilleur_score}")
    return True


#  oiseau ia  
class OiseauIA:
    """oiseau ia avec un cerveau, une position, une vitesse, un frame, un compteur d'animation, 
    un statut de vivant, un score, une fitness, un nombre de ticks de survie, un cerveau, et une teinte
    """
    def __init__(self, cerveau=None):
        self.x            = 80
        self.y            = float(HAUTEUR // 2)
        self.vitesse_y    = 0.0
        self.frame        = 0
        self.compteur_anim= 0
        self.vivant       = True
        self.score        = 0
        self.fitness      = 0
        self.ticks_survie = 0
        self.cerveau      = cerveau if cerveau else ReseauNeurones()
        # teinte légèrement différente par individu pour les distinguer
        self._alpha       = 180  # semi-transparent pour voir la foule

    def obtenir_entrees(self, tuyaux):
        """obtenir les entrees pour le reseau de neurones
        """
        # trouver le tuyau le plus proche
        prochain = None
        for t in tuyaux:
            if t.x + 65 > self.x - 10:
                prochain = t
                break
        # normaliser les entrees
        y_norm  = self.y / HAUTEUR_SOL
        vy_norm = self.vitesse_y / 15.0
        if prochain:
            dist_norm = (prochain.x - self.x) / LARGEUR
            trou_norm = prochain.centre_trou / HAUTEUR_SOL
            diff_norm = (self.y - prochain.centre_trou) / HAUTEUR_SOL
        else:
            dist_norm, trou_norm, diff_norm = 1.0, 0.5, 0.0
        return [y_norm, vy_norm, dist_norm, trou_norm, diff_norm]

    def penser(self, tuyaux):
        """penser avec le reseau de neurones
        """
        if not self.vivant:
            return
        if self.cerveau.predire(self.obtenir_entrees(tuyaux)) > 0:
            self.vitesse_y = FORCE_SAUT

    def mise_a_jour(self):
        """mettre a jour l'oiseau
        """
        if not self.vivant:
            return
        self.vitesse_y     += GRAVITE
        self.y             += self.vitesse_y
        self.ticks_survie  += 1
        self.compteur_anim += 1
        if self.compteur_anim >= 5:
            self.compteur_anim = 0
            self.frame = (self.frame + 1) % 3

    def obtenir_rect(self):
        """obtenir le rectangle de l'oiseau
        """
        image = img_oiseau[self.frame]
        rect  = image.get_rect(center=(self.x, int(self.y)))
        return rect.inflate(-6, -6)

    def dessiner(self, surface):
        if not self.vivant:
            return
        image = img_oiseau[self.frame]
        angle = -self.vitesse_y * 3
        angle = max(-90, min(angle, 25))
        image_tournee = pygame.transform.rotate(image, angle)
        # surface temporaire pour appliquer la transparence
        tmp = pygame.Surface(image_tournee.get_size(), pygame.SRCALPHA)
        tmp.blit(image_tournee, (0, 0))
        tmp.set_alpha(self._alpha)
        rect = image_tournee.get_rect(center=(self.x, int(self.y)))
        surface.blit(tmp, rect)


#  tuyau  
class Tuyau:
    LARGEUR_IMG = 65
    HAUTEUR_IMG = 400

    def __init__(self, x):
        self.x           = x
        self.centre_trou = random.randint(130, HAUTEUR_SOL - 130)
        self.deja_passe  = False

    def mise_a_jour(self):
        self.x -= VITESSE_JEU

    def est_hors_ecran(self):
        return self.x + self.LARGEUR_IMG < 0

    def obtenir_rects(self):
        y_haut = self.centre_trou - ESPACE_TUYAUX // 2 - self.HAUTEUR_IMG
        y_bas  = self.centre_trou + ESPACE_TUYAUX // 2
        return (
            pygame.Rect(self.x, y_haut, self.LARGEUR_IMG, self.HAUTEUR_IMG),
            pygame.Rect(self.x, y_bas,  self.LARGEUR_IMG, self.HAUTEUR_IMG)
        )

    def collision(self, rect):
        for r in self.obtenir_rects():
            if rect.colliderect(r):
                return True
        return False

    def dessiner(self, surface):
        y_haut = self.centre_trou - ESPACE_TUYAUX // 2 - self.HAUTEUR_IMG
        y_bas  = self.centre_trou + ESPACE_TUYAUX // 2
        surface.blit(img_tuyau_haut, (self.x, y_haut))
        surface.blit(img_tuyau_bas,  (self.x, y_bas))


#  sol 
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


#  score 
def afficher_score(surface, score, y=50):
    texte         = str(score)
    largeur_totale = len(texte) * 30
    x_depart      = (LARGEUR - largeur_totale) // 2
    for i, c in enumerate(texte):
        surface.blit(img_chiffres[int(c)], (x_depart + i * 30, y))


#  algorithme genetique
class NEAT:
    # fonction d'initialisation
    def __init__(self, taille=TAILLE_POPULATION):
        self.taille            = taille
        self.generation        = 1
        self.meilleur_score    = 0
        self.meilleur_fitness  = 0
        self.meilleur_cerveau  = None
        self.historique_scores = []
        self.population        = [OiseauIA() for _ in range(taille)]

    # fonction de calcul de la fitness 
    def calculer_fitness(self, o):
        o.fitness = o.ticks_survie + o.score * 1000
#la fitness est la somme du nombre de ticks de survie et du score multiplié par 1000

    # fonction de selection des oiseaux
    def selectionner(self, pop_triee):
        candidats = random.sample(pop_triee[:max(5, len(pop_triee)//2)], 2)
        return candidats[0], candidats[1]

    # fonction de nouvelle generation
    def nouvelle_generation(self):
        for o in self.population:
            self.calculer_fitness(o)
        self.population.sort(key=lambda o: o.fitness, reverse=True)
        meilleur = self.population[0]
        if meilleur.score   > self.meilleur_score:
            self.meilleur_score = meilleur.score
        if meilleur.fitness > self.meilleur_fitness:
            self.meilleur_fitness = meilleur.fitness
            self.meilleur_cerveau = meilleur.cerveau.copier()
        self.historique_scores.append(meilleur.score)

        nouvelle_pop = []
        # Élitisme : 2 meilleurs intacts
        for i in range(2):
            elite = OiseauIA(self.population[i].cerveau.copier())
            elite._alpha = 255
            nouvelle_pop.append(elite)
        # Reste : croisement + mutation
        stagnation = len(self.historique_scores) > 5 and max(self.historique_scores[-5:]) == self.historique_scores[-1]
        taux = TAUX_MUTATION * 3 if stagnation else TAUX_MUTATION
        while len(nouvelle_pop) < self.taille:
            p1, p2 = self.selectionner(self.population)
            cerveau = ReseauNeurones.croisement(p1.cerveau, p2.cerveau) if random.random() < TAUX_CROISEMENT else p1.cerveau.copier()
            cerveau.muter(taux)
            nouvelle_pop.append(OiseauIA(cerveau))
        self.population = nouvelle_pop
        self.generation += 1


#  panneau info 
def dessiner_panneau(surface, neat, nb_vivants, score_actuel, vitesse):
    panel = pygame.Surface((155, 310), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 160))
    surface.blit(panel, (LARGEUR - 160, 5))

    x, y = LARGEUR - 153, 12

    def ligne(texte, couleur=BLANC, dy=18):
        nonlocal y
        surface.blit(font_small.render(texte, True, couleur), (x, y))
        y += dy

    ligne(f"GEN     : {neat.generation}",          CYAN)
    ligne(f"VIVANTS : {nb_vivants}/{neat.taille}", JAUNE)
    ligne(f"SCORE   : {score_actuel}",              BLANC)
    ligne(f"BEST    : {neat.meilleur_score}",       ORANGE)
    ligne(f"VITESSE : x{vitesse:.1f}",              GRIS_CLAIR)
    ligne("─" * 17, GRIS)

    ligne("SCORES PAR GEN:", GRIS_CLAIR, dy=15)
    if len(neat.historique_scores) > 1:
        scores = neat.historique_scores[-20:]
        max_s  = max(scores) if max(scores) > 0 else 1
        gw, gh = 138, 45
        gx, gy = x, y
        pygame.draw.rect(surface, (20, 20, 20), (gx, gy, gw, gh))
        for i in range(1, len(scores)):
            x1 = gx + (i - 1) * gw // (len(scores) - 1)
            y1 = gy + gh - int(scores[i-1] / max_s * (gh - 4))
            x2 = gx + i * gw // (len(scores) - 1)
            y2 = gy + gh - int(scores[i]   / max_s * (gh - 4))
            pygame.draw.line(surface, CYAN, (x1, y1), (x2, y2), 2)
        y += gh + 4

    ligne("─" * 17, GRIS)
    ligne("ESPACE : pause",   GRIS_CLAIR, dy=15)
    ligne("↑/↓   : vitesse",  GRIS_CLAIR, dy=15)
    ligne("R      : reset",   GRIS_CLAIR, dy=15)
    save_ok = os.path.exists(FICHIER_SAVE)
    ligne("SAVE: " + ("✓ OK" if save_ok else "aucune"), VERT if save_ok else ROUGE, dy=15)


#  boucle principale
def main():
    neat        = NEAT(TAILLE_POPULATION)
    charger(neat)
    tuyaux      = []
    sol         = Sol()
    score_actuel = 0
    en_pause    = False
    vitesse_sim = 1.0
    tick_acc    = 0.0

    while True:
        horloge.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sauvegarder(neat)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    en_pause = not en_pause
                elif event.key == pygame.K_UP:
                    vitesse_sim = min(vitesse_sim + 0.5, 10.0)
                elif event.key == pygame.K_DOWN:
                    vitesse_sim = max(vitesse_sim - 0.5, 0.5)
                elif event.key == pygame.K_r:
                    for o in neat.population:
                        o.vivant = False

        if en_pause:
            # redessine le fond pour ne pas freeze
            ecran.blit(img_fond, (0, 0))
            for t in tuyaux:
                t.dessiner(ecran)
            sol.dessiner(ecran)
            for o in neat.population:
                o.dessiner(ecran)
            overlay = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            ecran.blit(overlay, (0, 0))
            txt = font_large.render("PAUSE  (ESPACE)", True, BLANC)
            ecran.blit(txt, txt.get_rect(center=(LARGEUR // 2, HAUTEUR // 2)))
            pygame.display.flip()
            continue

        # simulation accélérée
        tick_acc += vitesse_sim
        nb_ticks  = int(tick_acc)
        tick_acc -= nb_ticks

        for _ in range(max(1, nb_ticks)):
            # tuyaux
            if not tuyaux or tuyaux[-1].x < LARGEUR - INTERVALLE_TUYAUX:
                tuyaux.append(Tuyau(LARGEUR))
            for t in tuyaux:
                t.mise_a_jour()
            tuyaux = [t for t in tuyaux if not t.est_hors_ecran()]

            sol.mise_a_jour()

            vivants = [o for o in neat.population if o.vivant]
            for o in vivants:
                o.penser(tuyaux)
                o.mise_a_jour()
                rect = o.obtenir_rect()
                mort = o.y >= HAUTEUR_SOL - 15 or o.y <= 0
                for t in tuyaux:
                    if t.collision(rect):
                        mort = True
                if mort:
                    o.vivant = False
                for t in tuyaux:
                    if not t.deja_passe and t.x + Tuyau.LARGEUR_IMG < o.x:
                        o.score      += 1
                        t.deja_passe  = True

            score_actuel = max((o.score for o in neat.population), default=0)
            if score_actuel > neat.meilleur_score:
                neat.meilleur_score = score_actuel

            if not any(o.vivant for o in neat.population):
                neat.nouvelle_generation()
                sauvegarder(neat)
                tuyaux       = []
                score_actuel = 0

        # dessin du fond
        ecran.blit(img_fond, (0, 0))

        for t in tuyaux:
            t.dessiner(ecran)

        sol.dessiner(ecran)

        # ligne de guidage du meilleur oiseau vivant
        vivants = [o for o in neat.population if o.vivant]
        if vivants and tuyaux:
            best = max(vivants, key=lambda o: o.score * 1000 + o.ticks_survie)
            for t in tuyaux:
                if t.x + 65 > best.x - 10:
                    pygame.draw.line(ecran, (255, 255, 0),
                                     (best.x, int(best.y)),
                                     (t.x, t.centre_trou), 1)
                    break

        for o in neat.population:
            o.dessiner(ecran)

        afficher_score(ecran, score_actuel)

        nb_vivants = sum(1 for o in neat.population if o.vivant)
        dessiner_panneau(ecran, neat, nb_vivants, score_actuel, vitesse_sim)

        pygame.display.flip()


if __name__ == "__main__":
    main()