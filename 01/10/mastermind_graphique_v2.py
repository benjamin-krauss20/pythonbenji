import json
import math
import os
import random
import re
import time
import tkinter as tk

COULEURS = "RVBJON"   # Rouge, Vert, Bleu, Jaune, Orange, Noir
LONGUEUR = 4
ESSAIS_MAX = 10
BILLES_PAR_COULEUR = 13

# Couleur d'affichage de chaque bille
TEINTES = {
    "R": "#e53935",
    "V": "#43a047",
    "B": "#1e88e5",
    "J": "#fdd835",
    "O": "#fb8c00",
    "N": "#212121",
}

# Dimensions
LARGEUR = 740
HAUTEUR = 650
LIGNE_H = 46          # hauteur d'une ligne d'essai
Y_SECRET = 95         # ligne du code secret
Y_PLATEAU = 135       # haut de la première ligne d'essai
X_TROUS = 85          # x du premier trou
ECART_TROUS = 55      # écart entre deux trous
R_TROU = 16           # rayon d'une bille sur le plateau
X_INDICES = 320       # x des petits pions d'indice
CACHE_X1, CACHE_X2 = 55, 280

# Le bac à billes
BAC_X1, BAC_Y1, BAC_X2, BAC_Y2 = 440, 135, 720, 595
R_BILLE = 15
FROTTEMENT = 0.92
REBOND = 0.5

# Thème (inspiré de la boîte Hasbro)
BLEU = "#123c7a"
PLAQUE = "#141414"
FENTE = "#262626"
TROU = "#050505"
SURBRILLANCE = "#2f2f2f"
JAUNE = "#ffd54f"
ROUGE_INDICE = "#e53935"
BLANC_INDICE = "#f5f5f5"

FICHIER_SCORES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benjimind_scores.json")


# ---------- Règles du jeu ----------

def generer_code():
    code = ""
    for i in range(LONGUEUR):
        code = code + random.choice(COULEURS)
    return code


def evaluer(code, prop):
    # Bien placés : même couleur à la même position
    bien_places = 0
    for i in range(LONGUEUR):
        if prop[i] == code[i]:
            bien_places = bien_places + 1

    # Couleurs communes (peu importe la position)
    communes = 0
    for c in COULEURS:
        communes = communes + min(code.count(c), prop.count(c))

    mal_places = communes - bien_places
    return bien_places, mal_places


def format_temps(secondes):
    s = int(secondes)
    return "%02d:%02d" % (s // 60, s % 60)


# ---------- Meilleurs scores ----------

def charger_scores():
    try:
        with open(FICHIER_SCORES, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def enregistrer_score(nom, essais, temps):
    """Ajoute un score et renvoie son rang (1 = meilleur), ou None s'il n'est pas dans le top 10."""
    scores = charger_scores()
    entree = {"nom": nom, "essais": essais, "temps": round(temps, 1),
              "date": time.strftime("%d/%m/%Y")}
    scores.append(entree)
    scores.sort(key=lambda s: (s["essais"], s["temps"]))
    scores = scores[:10]
    try:
        with open(FICHIER_SCORES, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
    for i, s in enumerate(scores):
        if s is entree:
            return i + 1
    return None


def afficher_scores(fenetre, surligner=None):
    fen = tk.Toplevel(fenetre, bg=PLAQUE, padx=20, pady=15)
    fen.title("Meilleurs scores")
    fen.resizable(False, False)
    tk.Label(fen, text="Meilleurs scores", fg=JAUNE, bg=PLAQUE,
             font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=5, pady=(0, 10))
    entetes = ["#", "Nom", "Essais", "Temps", "Date"]
    for col, texte in enumerate(entetes):
        tk.Label(fen, text=texte, fg="#aaaaaa", bg=PLAQUE,
                 font=("Arial", 10, "bold")).grid(row=1, column=col, padx=8)
    scores = charger_scores()
    if not scores:
        tk.Label(fen, text="Aucun score pour l'instant.", fg="white", bg=PLAQUE,
                 font=("Arial", 11)).grid(row=2, column=0, columnspan=5, pady=10)
    for i, s in enumerate(scores):
        couleur = JAUNE if surligner == i + 1 else "white"
        valeurs = [str(i + 1), s["nom"], str(s["essais"]), format_temps(s["temps"]), s["date"]]
        for col, texte in enumerate(valeurs):
            tk.Label(fen, text=texte, fg=couleur, bg=PLAQUE,
                     font=("Arial", 11)).grid(row=i + 2, column=col, padx=8, pady=1)
    tk.Button(fen, text="Fermer", command=fen.destroy).grid(row=20, column=0, columnspan=5, pady=(12, 0))
    fen.transient(fenetre)
    fen.lift()


# ---------- Dessin d'une bille ----------

def melanger(c1, c2, t):
    """Mélange deux couleurs hexadécimales (t=0 -> c1, t=1 -> c2)."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    return "#%02x%02x%02x" % (int(r1 + (r2 - r1) * t), int(g1 + (g2 - g1) * t), int(b1 + (b2 - b1) * t))


def dessiner_bille(cv, x, y, r, couleur, tags):
    base = TEINTES.get(couleur, couleur)
    cv.create_oval(x - r, y - r, x + r, y + r, fill=base,
                   outline=melanger(base, "#000000", 0.5), width=2, tags=tags)
    # reflets pour donner un effet de bille en verre
    cv.create_oval(x - r * 0.65, y - r * 0.7, x + r * 0.1, y - r * 0.05,
                   fill=melanger(base, "#ffffff", 0.3), outline="", tags=tags)
    cv.create_oval(x - r * 0.5, y - r * 0.55, x - r * 0.15, y - r * 0.25,
                   fill=melanger(base, "#ffffff", 0.8), outline="", tags=tags)


class Bille:
    compteur = 0

    def __init__(self, couleur, x, y):
        Bille.compteur = Bille.compteur + 1
        self.c = couleur
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.tag = "b" + str(Bille.compteur)
        self.cible = None     # destination quand la bille "vole" vers le bac


def dans_bac(x, y):
    return BAC_X1 < x < BAC_X2 and BAC_Y1 < y < BAC_Y2


# ---------- Le jeu ----------

class Mastermind:
    def __init__(self, fenetre, noms):
        self.fenetre = fenetre
        self.noms = noms
        self.deux = len(noms) == 2
        self.codeur = 0              # en mode 2 joueurs : qui compose le code
        self.points = [0, 0]
        self.phase = None            # "composer", "deviner" ou "fini"
        fenetre.title("BenjiMind")
        fenetre.resizable(False, False)

        self.cadre = tk.Frame(fenetre, bg=BLEU)
        self.cadre.pack()
        self.cv = tk.Canvas(self.cadre, width=LARGEUR, height=HAUTEUR, bg=BLEU, highlightthickness=0)
        self.cv.pack()

        barre = tk.Frame(self.cadre, bg=BLEU)
        barre.pack(fill="x", pady=(0, 10))
        self.bouton_valider = tk.Button(barre, text="Valider", font=("Arial", 12, "bold"),
                                        width=13, command=self.valider)
        self.bouton_valider.pack(side="left", padx=(15, 5))
        tk.Button(barre, text="Vider la ligne", font=("Arial", 10),
                  command=self.vider_ligne).pack(side="left", padx=5)
        tk.Button(barre, text="Secouer le bac", font=("Arial", 10),
                  command=self.secouer).pack(side="left", padx=5)
        tk.Button(barre, text="Menu", font=("Arial", 10),
                  command=self.menu).pack(side="right", padx=(5, 15))
        tk.Button(barre, text="Meilleurs scores", font=("Arial", 10),
                  command=lambda: afficher_scores(fenetre)).pack(side="right", padx=5)
        tk.Button(barre, text="Nouvelle manche" if self.deux else "Nouvelle partie",
                  font=("Arial", 10), command=self.nouvelle_partie).pack(side="right", padx=5)

        # Textes qui changent souvent (chrono, points, consigne)
        self.texte_chrono = self.cv.create_text((BAC_X1 + BAC_X2) // 2, 30, text="",
                                                fill="white", font=("Consolas", 20, "bold"))
        self.texte_points = self.cv.create_text((BAC_X1 + BAC_X2) // 2, 72, text="",
                                                fill=JAUNE, font=("Arial", 11, "bold"))
        self.texte_consigne = self.cv.create_text(LARGEUR // 2, 628, text="",
                                                  fill="white", font=("Arial", 10))

        self.cv.bind("<ButtonPress-1>", self.clic)
        self.cv.bind("<B1-Motion>", self.glisser)
        self.cv.bind("<ButtonRelease-1>", self.relacher)
        self.cv.bind("<Button-3>", self.clic_droit)

        # Remplissage du bac
        self.bac = []           # billes posées dans le bac
        self.volantes = []      # billes qui volent vers le bac
        self.tenue = None       # bille tenue par la souris
        self.animations = []
        couleurs = list(COULEURS) * BILLES_PAR_COULEUR
        random.shuffle(couleurs)
        for c in couleurs:
            x, y = self.place_libre()
            self.bac.append(self.creer_bille(c, x, y))

        self.nouvelle_partie()
        self.boucle()

    # ---------- Partie ----------

    def nouvelle_partie(self):
        if self.deux and self.phase == "fini":
            self.codeur = 1 - self.codeur      # on inverse les rôles à chaque manche

        # Les billes de la ligne en cours retournent dans le bac
        if self.phase in ("composer", "deviner"):
            for i in range(LONGUEUR):
                if self.proposition[i]:
                    x, y = self.pos_trou(i)
                    self.renvoyer(self.proposition[i], x, y)

        self.cv.delete("effet")
        self.animations = []
        self.essai = 0                       # index de la ligne en cours
        self.proposition = [None] * LONGUEUR
        self.historique = []                 # liste de (prop, bien, mal)
        self.lignes_grises = set()
        self.debut = time.monotonic()
        self.temps_final = None
        if self.deux:
            self.code = None
            self.phase = "composer"
            self.ouverture = 1.0               # cache ouvert pour que le codeur voie son code
        else:
            self.code = generer_code()
            self.phase = "deviner"
            self.ouverture = 0.0
        self.dessiner()
        self.maj_textes()

    def devineur(self):
        return self.noms[1 - self.codeur] if self.deux else self.noms[0]

    def valider(self):
        if None in self.proposition:
            return
        prop = "".join(self.proposition)

        if self.phase == "composer":
            self.code = prop
            self.proposition = [None] * LONGUEUR
            self.remplir_bac(prop)
            self.phase = "deviner"
            self.debut = time.monotonic()
            self.lancer(self.anim_cache(ouvrir=False))
            self.dessiner()
            self.maj_textes()
            return

        if self.phase != "deviner":
            return
        bien, mal = evaluer(self.code, prop)
        self.historique.append((prop, bien, mal))
        self.proposition = [None] * LONGUEUR
        self.remplir_bac(prop)
        self.essai = self.essai + 1

        if bien == LONGUEUR:
            self.fin(True)
        elif self.essai >= ESSAIS_MAX:
            self.fin(False)
        else:
            self.dessiner()

    def fin(self, gagne):
        self.phase = "fini"
        self.temps_final = time.monotonic() - self.debut
        temps = format_temps(self.temps_final)
        self.dessiner()
        self.lancer(self.anim_cache(ouvrir=True))

        nom = self.devineur()
        if not self.deux:
            if gagne:
                lignes = ["Bravo " + nom + " !", "Code trouvé en " + str(self.essai) + " essai(s) — " + temps]
                rang = enregistrer_score(nom, self.essai, self.temps_final)
                if rang == 1:
                    lignes.append("★ Nouveau record ! ★")
                elif rang:
                    lignes.append(str(rang) + "e au tableau des scores")
            else:
                lignes = ["Perdu " + nom + " !", "Le code secret est dévoilé en haut."]
        else:
            codeur = self.noms[self.codeur]
            if gagne:
                pts = self.essai
                lignes = ["Bravo " + nom + " !", "Trouvé en " + str(self.essai) + " essai(s) — " + temps]
            else:
                pts = ESSAIS_MAX + 1
                lignes = [nom + " n'a pas trouvé !"]
            self.points[self.codeur] = self.points[self.codeur] + pts
            lignes.append(codeur + " marque " + str(pts) + " point(s)")
            lignes.append(self.noms[0] + " " + str(self.points[0]) + "  –  "
                          + str(self.points[1]) + " " + self.noms[1])

        if gagne:
            self.lancer(self.anim_pulsation(self.essai - 1))
            self.lancer(self.anim_confettis())
            self.lancer(self.anim_banniere(lignes, gagne=True, delai=15))
        else:
            self.lancer(self.anim_defaite())
            self.lancer(self.anim_banniere(lignes, gagne=False, delai=10))
        self.maj_textes()

    def vider_ligne(self):
        if self.phase not in ("composer", "deviner"):
            return
        for i in range(LONGUEUR):
            if self.proposition[i]:
                x, y = self.pos_trou(i)
                self.renvoyer(self.proposition[i], x, y)
                self.proposition[i] = None
        self.dessiner()

    def secouer(self):
        for b in self.bac:
            b.vx = b.vx + random.uniform(-10, 10)
            b.vy = b.vy + random.uniform(-10, 10)

    def menu(self):
        self.fenetre.after_cancel(self.id_boucle)
        self.cadre.destroy()
        afficher_accueil(self.fenetre)

    # ---------- Bac à billes ----------

    def creer_bille(self, couleur, x, y):
        b = Bille(couleur, x, y)
        dessiner_bille(self.cv, x, y, R_BILLE, couleur, ("bille", b.tag))
        return b

    def place_libre(self):
        """Cherche un endroit du bac où poser une bille sans chevaucher les autres."""
        for essai in range(200):
            x = random.uniform(BAC_X1 + R_BILLE, BAC_X2 - R_BILLE)
            y = random.uniform(BAC_Y1 + R_BILLE, BAC_Y2 - R_BILLE)
            if all((x - b.x) ** 2 + (y - b.y) ** 2 >= (2 * R_BILLE) ** 2 for b in self.bac):
                return x, y
        return x, y

    def renvoyer(self, couleur, x, y):
        """Une bille quitte le plateau et vole jusqu'au bac."""
        b = self.creer_bille(couleur, x, y)
        b.cible = self.place_libre()
        self.volantes.append(b)

    def remplir_bac(self, prop):
        # Les billes posées sur le plateau y restent : de nouvelles arrivent dans le bac
        for c in prop:
            self.renvoyer(c, random.uniform(BAC_X1, BAC_X2), -20)

    def physique(self):
        cv = self.cv
        anciennes = [(b.x, b.y) for b in self.bac]

        # Billes qui volent vers le bac
        for b in self.volantes[:]:
            dx = b.cible[0] - b.x
            dy = b.cible[1] - b.y
            mx, my = dx * 0.15, dy * 0.15
            b.x, b.y = b.x + mx, b.y + my
            cv.move(b.tag, mx, my)
            if dx * dx + dy * dy < 4:
                self.volantes.remove(b)
                b.vx, b.vy = mx, my
                self.bac.append(b)
                anciennes.append((b.x, b.y))

        # Déplacement + frottement
        for b in self.bac:
            b.vx = b.vx * FROTTEMENT
            b.vy = b.vy * FROTTEMENT
            b.x = b.x + b.vx
            b.y = b.y + b.vy

        # Chocs entre billes
        d_min = 2 * R_BILLE
        n = len(self.bac)
        for i in range(n):
            a = self.bac[i]
            for j in range(i + 1, n):
                b = self.bac[j]
                dx = b.x - a.x
                if dx > d_min or dx < -d_min:
                    continue
                dy = b.y - a.y
                if dy > d_min or dy < -d_min:
                    continue
                d2 = dx * dx + dy * dy
                if d2 >= d_min * d_min or d2 == 0:
                    continue
                d = math.sqrt(d2)
                nx, ny = dx / d, dy / d
                recouvrement = (d_min - d) / 2
                a.x, a.y = a.x - nx * recouvrement, a.y - ny * recouvrement
                b.x, b.y = b.x + nx * recouvrement, b.y + ny * recouvrement
                rel = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
                if rel < 0:
                    impulsion = -rel * 0.9
                    a.vx, a.vy = a.vx - impulsion * nx, a.vy - impulsion * ny
                    b.vx, b.vy = b.vx + impulsion * nx, b.vy + impulsion * ny

        # La bille tenue pousse les autres
        t = self.tenue
        if t:
            for b in self.bac:
                dx, dy = b.x - t.x, b.y - t.y
                d2 = dx * dx + dy * dy
                if 0 < d2 < d_min * d_min:
                    d = math.sqrt(d2)
                    nx, ny = dx / d, dy / d
                    b.x, b.y = b.x + nx * (d_min - d), b.y + ny * (d_min - d)
                    b.vx = b.vx + nx * (d_min - d) * 0.4 + t.vx * 0.2
                    b.vy = b.vy + ny * (d_min - d) * 0.4 + t.vy * 0.2

        # Les bords du bac
        for b in self.bac:
            if b.x < BAC_X1 + R_BILLE:
                b.x, b.vx = BAC_X1 + R_BILLE, abs(b.vx) * REBOND
            elif b.x > BAC_X2 - R_BILLE:
                b.x, b.vx = BAC_X2 - R_BILLE, -abs(b.vx) * REBOND
            if b.y < BAC_Y1 + R_BILLE:
                b.y, b.vy = BAC_Y1 + R_BILLE, abs(b.vy) * REBOND
            elif b.y > BAC_Y2 - R_BILLE:
                b.y, b.vy = BAC_Y2 - R_BILLE, -abs(b.vy) * REBOND

        # On ne redessine que les billes qui ont bougé
        for b, (x0, y0) in zip(self.bac, anciennes):
            if abs(b.x - x0) > 0.01 or abs(b.y - y0) > 0.01:
                cv.move(b.tag, b.x - x0, b.y - y0)

    def boucle(self):
        self.physique()
        for anim in self.animations[:]:
            try:
                next(anim)
            except StopIteration:
                self.animations.remove(anim)
        self.maj_chrono()
        self.id_boucle = self.fenetre.after(16, self.boucle)

    def lancer(self, anim):
        self.animations.append(anim)

    # ---------- Souris ----------

    def ligne_active_y(self):
        return Y_SECRET if self.phase == "composer" else self.y_ligne(self.essai)

    def pos_trou(self, i):
        return X_TROUS + i * ECART_TROUS, self.ligne_active_y()

    def trou_sous(self, x, y):
        """Renvoie l'index du trou de la ligne en cours sous la souris, ou None."""
        if self.phase not in ("composer", "deviner"):
            return None
        for i in range(LONGUEUR):
            cx, cy = self.pos_trou(i)
            if (x - cx) ** 2 + (y - cy) ** 2 <= (R_TROU + 8) ** 2:
                return i
        return None

    def clic(self, event):
        # Un clic sur la bannière de fin la fait disparaître
        if "banniere" in self.cv.gettags("current"):
            self.cv.delete("banniere")
            return
        if self.phase not in ("composer", "deviner"):
            return

        for b in reversed(self.bac):
            if (event.x - b.x) ** 2 + (event.y - b.y) ** 2 <= (R_BILLE + 2) ** 2:
                # On attrape une bille dans le bac
                self.bac.remove(b)
                b.vx = b.vy = 0
                self.tenue = b
                self.cv.tag_raise(b.tag)
                return

        trou = self.trou_sous(event.x, event.y)
        if trou is not None and self.proposition[trou]:
            # On reprend une bille déjà posée sur la ligne
            self.tenue = self.creer_bille(self.proposition[trou], event.x, event.y)
            self.proposition[trou] = None
            self.dessiner()

    def glisser(self, event):
        b = self.tenue
        if b:
            dx, dy = event.x - b.x, event.y - b.y
            b.vx, b.vy = 0.5 * b.vx + 0.5 * dx, 0.5 * b.vy + 0.5 * dy
            b.x, b.y = event.x, event.y
            self.cv.move(b.tag, dx, dy)

    def relacher(self, event):
        b = self.tenue
        if not b:
            return
        self.tenue = None
        trou = self.trou_sous(event.x, event.y)
        if trou is not None:
            ancienne = self.proposition[trou]
            self.proposition[trou] = b.c
            self.cv.delete(b.tag)
            if ancienne:
                x, y = self.pos_trou(trou)
                self.renvoyer(ancienne, x, y)
            self.dessiner()
        elif dans_bac(b.x, b.y):
            # Lâchée dans le bac : elle roule avec l'élan du geste
            b.vx = max(-12, min(12, b.vx))
            b.vy = max(-12, min(12, b.vy))
            self.bac.append(b)
        else:
            b.cible = self.place_libre()
            self.volantes.append(b)

    def clic_droit(self, event):
        # Clic droit sur une bille de la ligne en cours : elle retourne au bac
        trou = self.trou_sous(event.x, event.y)
        if trou is not None and self.proposition[trou]:
            x, y = self.pos_trou(trou)
            self.renvoyer(self.proposition[trou], x, y)
            self.proposition[trou] = None
            self.dessiner()

    # ---------- Dessin ----------

    def y_ligne(self, n):
        return Y_PLATEAU + n * LIGNE_H + LIGNE_H // 2

    def trou_vide(self, x, y, tags):
        r = R_TROU * 0.55
        self.cv.create_oval(x - r, y - r, x + r, y + r, fill=TROU, outline="#3a3a3a", width=1, tags=tags)

    def dessiner(self):
        cv = self.cv
        cv.delete("plateau")
        t = "plateau"

        # Titre
        cv.create_text(218, 31, text="BenjiMind", fill="#b71c1c", font=("Arial Black", 24), tags=t)
        cv.create_text(215, 28, text="BenjiMind", fill=JAUNE, font=("Arial Black", 24), tags=t)

        # Plateau noir
        cv.create_rectangle(15, 55, 415, 605, fill=PLAQUE, outline="#000000", width=3, tags=t)

        # Ligne du code secret
        couleur_cadre = JAUNE if self.phase == "composer" else "#444444"
        cv.create_rectangle(CACHE_X1, 70, CACHE_X2, 120, fill=FENTE, outline=couleur_cadre, width=2, tags=t)
        secret = self.proposition if self.phase == "composer" else (self.code or [None] * LONGUEUR)
        for i in range(LONGUEUR):
            x = X_TROUS + i * ECART_TROUS
            if secret[i]:
                dessiner_bille(cv, x, Y_SECRET, R_TROU, secret[i], t)
            else:
                self.trou_vide(x, Y_SECRET, t)
        cv.create_text(355, 85, text="● bien placé", fill=ROUGE_INDICE, font=("Arial", 9, "bold"), tags=t)
        cv.create_text(355, 105, text="● mal placé", fill=BLANC_INDICE, font=("Arial", 9, "bold"), tags=t)

        # Lignes d'essai
        for n in range(ESSAIS_MAX):
            y = self.y_ligne(n)
            if n == self.essai and self.phase == "deviner":
                cv.create_rectangle(22, y - LIGNE_H // 2 + 3, 408, y + LIGNE_H // 2 - 3,
                                    fill=SURBRILLANCE, outline=JAUNE, width=2, tags=t)
            cv.create_text(38, y, text=str(n + 1), fill="#888888", font=("Arial", 11, "bold"), tags=t)

            bien, mal = None, None
            if n < len(self.historique):
                prop, bien, mal = self.historique[n]
                couleurs = list(prop)
            elif n == self.essai and self.phase == "deviner":
                couleurs = self.proposition
            else:
                couleurs = [None] * LONGUEUR

            for i in range(LONGUEUR):
                x = X_TROUS + i * ECART_TROUS
                if couleurs[i]:
                    c = "#5a5a5a" if n in self.lignes_grises else couleurs[i]
                    dessiner_bille(cv, x, y, R_TROU, c, t)
                else:
                    self.trou_vide(x, y, t)

            # Petits pions d'indice en carré 2x2
            indices = []
            if bien is not None:
                indices = [ROUGE_INDICE] * bien + [BLANC_INDICE] * mal
            for k in range(LONGUEUR):
                ix = X_INDICES + (k % 2) * 18
                iy = y - 9 + (k // 2) * 18
                if k < len(indices):
                    cv.create_oval(ix - 6, iy - 6, ix + 6, iy + 6, fill=indices[k], outline="#000000", tags=t)
                else:
                    cv.create_oval(ix - 3, iy - 3, ix + 3, iy + 3, fill=TROU, outline="#3a3a3a", tags=t)

        # Le bac
        cv.create_text((BAC_X1 + BAC_X2) // 2, 115, text="Bac à billes", fill="white",
                       font=("Arial", 11, "bold"), tags=t)
        cv.create_rectangle(BAC_X1 - 8, BAC_Y1 - 8, BAC_X2 + 8, BAC_Y2 + 8, fill=PLAQUE,
                            outline="#000000", width=3, tags=t)
        cv.create_rectangle(BAC_X1, BAC_Y1, BAC_X2, BAC_Y2, fill="#1f1f1f", outline="#333333", tags=t)

        cv.tag_lower("plateau")
        self.dessiner_cache()

        # Bouton Valider
        if self.phase == "composer":
            self.bouton_valider.config(text="Cacher le code")
        else:
            self.bouton_valider.config(text="Valider")
        if self.phase in ("composer", "deviner") and None not in self.proposition:
            self.bouton_valider.config(state="normal")
        else:
            self.bouton_valider.config(state="disabled")

    def dessiner_cache(self):
        """Le volet qui cache le code secret (self.ouverture : 0 = fermé, 1 = ouvert)."""
        cv = self.cv
        cv.delete("cache")
        largeur = (CACHE_X2 - CACHE_X1) * (1 - self.ouverture)
        if largeur > 1:
            x2 = CACHE_X1 + largeur
            cv.create_rectangle(CACHE_X1, 70, x2, 120, fill="#3b3b3b", outline="#777777",
                                width=2, tags="cache")
            for i in range(LONGUEUR):
                x = X_TROUS + i * ECART_TROUS
                if x < x2 - 12:
                    cv.create_text(x, Y_SECRET, text="?", fill="#bbbbbb",
                                   font=("Arial", 16, "bold"), tags="cache")
        if cv.find_withtag("plateau"):
            cv.tag_raise("cache", "plateau")

    def maj_textes(self):
        if self.deux:
            self.cv.itemconfig(self.texte_points, text="Points : " + self.noms[0] + " " + str(self.points[0])
                               + "  –  " + str(self.points[1]) + " " + self.noms[1])
            codeur = self.noms[self.codeur]
            if self.phase == "composer":
                consigne = codeur + " : compose le code secret — " + self.devineur() + ", ne regarde pas !"
            elif self.phase == "deviner":
                consigne = self.devineur() + " : trouve le code de " + codeur \
                           + " (le codeur marque 1 point par essai)"
            else:
                consigne = "Clique sur « Nouvelle manche » : les rôles s'inversent."
        else:
            if self.phase == "deviner":
                consigne = "Attrape des billes dans le bac et pose-les sur la ligne jaune. Clic droit : remettre au bac."
            else:
                consigne = "Clique sur « Nouvelle partie » pour rejouer."
        self.cv.itemconfig(self.texte_consigne, text=consigne)

    def maj_chrono(self):
        if self.phase == "composer":
            secondes = 0
        elif self.temps_final is not None:
            secondes = self.temps_final
        else:
            secondes = time.monotonic() - self.debut
        texte = format_temps(secondes)
        if self.cv.itemcget(self.texte_chrono, "text") != texte:
            self.cv.itemconfig(self.texte_chrono, text=texte)

    # ---------- Animations (une étape par image) ----------

    def anim_cache(self, ouvrir):
        for k in range(1, 26):
            self.ouverture = k / 25 if ouvrir else 1 - k / 25
            self.dessiner_cache()
            yield

    def anim_pulsation(self, n):
        """Des ondes dorées autour de la ligne gagnante."""
        y = self.y_ligne(n)
        for cycle in range(4):
            for k in range(18):
                self.cv.delete("onde")
                r = R_TROU + k * 1.3
                for i in range(LONGUEUR):
                    x = X_TROUS + i * ECART_TROUS
                    self.cv.create_oval(x - r, y - r, x + r, y + r, outline=JAUNE,
                                        width=max(1, 4 - k // 5), tags=("onde", "effet"))
                yield
        self.cv.delete("onde")

    def anim_confettis(self):
        parts = []
        teintes = list(TEINTES.values()) + ["#ffffff", JAUNE]
        for _ in range(120):
            x = random.uniform(10, LARGEUR - 10)
            y = random.uniform(-250, -10)
            taille = random.randint(5, 9)
            item = self.cv.create_rectangle(x, y, x + taille, y + taille * 0.6, fill=random.choice(teintes),
                                            outline="", tags="effet")
            parts.append([item, random.uniform(-1.5, 1.5), random.uniform(0.5, 2), random.uniform(0, 6)])
        for f in range(260):
            for p in parts:
                p[2] = min(4, p[2] + 0.08)
                self.cv.move(p[0], p[1] + math.sin(f / 7 + p[3]) * 1.2, p[2])
            yield
        for p in parts:
            self.cv.delete(p[0])

    def anim_defaite(self):
        # La fenêtre tremble...
        fen = self.fenetre
        m = re.match(r"\d+x\d+\+(-?\d+)\+(-?\d+)", fen.geometry())
        if m:
            x0, y0 = int(m.group(1)), int(m.group(2))
            for k in range(24):
                amplitude = int(12 * (1 - k / 24))
                dx = amplitude if k % 2 == 0 else -amplitude
                fen.geometry("+%d+%d" % (x0 + dx, y0))
                yield
            fen.geometry("+%d+%d" % (x0, y0))
        # ... puis les billes du plateau s'éteignent une ligne après l'autre
        for n in reversed(range(len(self.historique))):
            self.lignes_grises.add(n)
            self.dessiner()
            for _ in range(4):
                yield

    def anim_banniere(self, lignes, gagne, delai):
        for _ in range(delai):
            yield
        cx, cy = 215, 340
        if gagne:
            # Elle grossit depuis le centre
            for k in range(1, 15):
                self.dessiner_banniere(cx, cy, lignes, k / 14, gagne)
                yield
        else:
            # Elle tombe du haut et rebondit
            y, v = -100.0, 0.0
            while True:
                v = v + 1.6
                y = y + v
                if y >= cy:
                    y = cy
                    v = -v * 0.45
                    if abs(v) < 2:
                        break
                self.dessiner_banniere(cx, y, lignes, 1, gagne)
                yield
            self.dessiner_banniere(cx, cy, lignes, 1, gagne)

    def dessiner_banniere(self, cx, cy, lignes, echelle, gagne):
        cv = self.cv
        cv.delete("banniere")
        tags = ("banniere", "effet")
        w = 360 * echelle
        h = (40 + 30 * len(lignes)) * echelle
        bord = JAUNE if gagne else "#e53935"
        cv.create_rectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, fill="#0d0d0d",
                            outline=bord, width=4, tags=tags)
        y = cy - h / 2 + 35 * echelle
        for i, texte in enumerate(lignes):
            taille = (20 if i == 0 else 12) * echelle
            if taille >= 4:
                couleur = bord if i == 0 else "white"
                cv.create_text(cx, y, text=texte, fill=couleur,
                               font=("Arial", int(taille), "bold"), tags=tags)
            y = y + 30 * echelle
        if echelle >= 1:
            cv.create_text(cx, cy + h / 2 - 10, text="(clic pour fermer)", fill="#777777",
                           font=("Arial", 8), tags=tags)


# ---------- Écran d'accueil ----------

def afficher_accueil(fenetre):
    fenetre.title("BenjiMind")
    fenetre.configure(bg=BLEU)
    accueil = tk.Frame(fenetre, bg=BLEU, padx=50, pady=30)
    accueil.pack()

    tk.Label(accueil, text="BenjiMind", fg=JAUNE, bg=BLEU, font=("Arial Black", 26)).pack(pady=(0, 15))

    mode = tk.StringVar(value="solo")
    choix = tk.Frame(accueil, bg=BLEU)
    choix.pack(pady=5)
    for texte, valeur in (("1 joueur", "solo"), ("2 joueurs", "duo")):
        tk.Radiobutton(choix, text=texte, value=valeur, variable=mode, font=("Arial", 12, "bold"),
                       fg="white", bg=BLEU, selectcolor=PLAQUE, activebackground=BLEU,
                       activeforeground=JAUNE, command=lambda: maj_mode()).pack(side="left", padx=10)

    tk.Label(accueil, text="Joueur 1 :", fg="white", bg=BLEU, font=("Arial", 12)).pack(pady=(10, 0))
    champ1 = tk.Entry(accueil, font=("Arial", 12), justify="center")
    champ1.pack(pady=5)
    champ1.focus_set()

    cadre2 = tk.Frame(accueil, bg=BLEU)
    tk.Label(cadre2, text="Joueur 2 :", fg="white", bg=BLEU, font=("Arial", 12)).pack()
    champ2 = tk.Entry(cadre2, font=("Arial", 12), justify="center")
    champ2.pack(pady=5)

    boutons = tk.Frame(accueil, bg=BLEU)
    boutons.pack(pady=(15, 0))

    def maj_mode():
        if mode.get() == "duo":
            cadre2.pack(before=boutons)
        else:
            cadre2.pack_forget()

    def commencer(event=None):
        noms = [champ1.get().strip() or "Joueur 1"]
        if mode.get() == "duo":
            noms.append(champ2.get().strip() or "Joueur 2")
        accueil.destroy()
        Mastermind(fenetre, noms)

    tk.Button(boutons, text="Jouer", font=("Arial", 12, "bold"), width=12, command=commencer).pack(pady=4)
    tk.Button(boutons, text="Meilleurs scores", font=("Arial", 10), width=15,
              command=lambda: afficher_scores(fenetre)).pack(pady=4)
    champ1.bind("<Return>", commencer)
    champ2.bind("<Return>", commencer)


def main():
    fenetre = tk.Tk()
    afficher_accueil(fenetre)

    # Force la fenêtre au premier plan (sinon elle peut s'ouvrir derrière VS Code)
    fenetre.lift()
    fenetre.attributes("-topmost", True)
    fenetre.after(300, lambda: fenetre.attributes("-topmost", False))
    fenetre.focus_force()

    fenetre.mainloop()


if __name__ == "__main__":
    main()
