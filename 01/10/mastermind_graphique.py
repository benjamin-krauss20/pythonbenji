import random
import tkinter as tk
from tkinter import messagebox

COULEURS = "RVBJON"   # Rouge, Vert, Bleu, Jaune, Orange, Noir
LONGUEUR = 4
ESSAIS_MAX = 10

# Couleur d'affichage de chaque pion
TEINTES = {
    "R": "#e53935",
    "V": "#43a047",
    "B": "#1e88e5",
    "J": "#fdd835",
    "O": "#fb8c00",
    "N": "#212121",
}
NOMS = {"R": "Rouge", "V": "Vert", "B": "Bleu", "J": "Jaune", "O": "Orange", "N": "Noir"}

# Dimensions du plateau
LARGEUR = 420
LIGNE_H = 44          # hauteur d'une ligne d'essai
Y_SECRET = 75         # ligne du code secret
Y_PLATEAU = 130       # première ligne d'essai
X_TROUS = 80          # x du premier trou
ECART_TROUS = 50      # écart entre deux trous
R_TROU = 15           # rayon d'un pion
X_INDICES = 300       # x des petits pions d'indice
Y_PALETTE = Y_PLATEAU + ESSAIS_MAX * LIGNE_H + 40
R_PALETTE = 20
HAUTEUR = Y_PALETTE + 45

FOND = "#6d4c41"
TROU = "#3e2723"
SURBRILLANCE = "#8d6e63"


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


class Mastermind:
    def __init__(self, fenetre, nom):
        self.fenetre = fenetre
        self.nom = nom
        fenetre.title("BenjiMind")
        fenetre.resizable(False, False)

        self.canvas = tk.Canvas(fenetre, width=LARGEUR, height=HAUTEUR, bg=FOND, highlightthickness=0)
        self.canvas.pack()

        barre = tk.Frame(fenetre, bg=FOND)
        barre.pack(fill="x")
        self.bouton_valider = tk.Button(barre, text="Valider", font=("Arial", 12, "bold"),
                                        width=10, command=self.valider)
        self.bouton_valider.pack(side="left", padx=20, pady=10)
        self.bouton_effacer = tk.Button(barre, text="Effacer la ligne", font=("Arial", 11),
                                        command=self.effacer_ligne)
        self.bouton_effacer.pack(side="left", pady=10)
        tk.Button(barre, text="Nouvelle partie", font=("Arial", 11),
                  command=self.nouvelle_partie).pack(side="right", padx=20, pady=10)

        self.canvas.bind("<ButtonPress-1>", self.clic)
        self.canvas.bind("<B1-Motion>", self.glisser)
        self.canvas.bind("<ButtonRelease-1>", self.relacher)
        self.canvas.bind("<Button-3>", self.clic_droit)

        self.nouvelle_partie()

    # ---------- Partie ----------

    def nouvelle_partie(self):
        self.code = generer_code()
        self.essai = 0                       # index de la ligne en cours
        self.proposition = [None] * LONGUEUR
        self.historique = []                 # liste de (prop, bien, mal)
        self.couleur_choisie = None
        self.pion_glisse = None
        self.fini = False
        self.dessiner()

    def valider(self):
        if self.fini or None in self.proposition:
            return
        prop = "".join(self.proposition)
        bien, mal = evaluer(self.code, prop)
        self.historique.append((prop, bien, mal))
        self.proposition = [None] * LONGUEUR
        self.essai = self.essai + 1

        if bien == LONGUEUR:
            self.fini = True
            self.dessiner()
            messagebox.showinfo("Gagné !", "Bravo " + self.nom + " ! Vous avez trouvé le code en "
                                + str(self.essai) + " essai(s) !")
        elif self.essai >= ESSAIS_MAX:
            self.fini = True
            self.dessiner()
            messagebox.showinfo("Perdu", "Perdu " + self.nom + " ! Le code est affiché en haut.")
        else:
            self.dessiner()

    def effacer_ligne(self):
        if not self.fini:
            self.proposition = [None] * LONGUEUR
            self.dessiner()

    # ---------- Souris ----------

    def trou_sous(self, x, y):
        """Renvoie l'index du trou de la ligne en cours sous la souris, ou None."""
        if self.fini:
            return None
        cy = self.y_ligne(self.essai)
        for i in range(LONGUEUR):
            cx = X_TROUS + i * ECART_TROUS
            if (x - cx) ** 2 + (y - cy) ** 2 <= (R_TROU + 5) ** 2:
                return i
        return None

    def couleur_sous(self, x, y):
        """Renvoie la couleur de la palette sous la souris, ou None."""
        for i, c in enumerate(COULEURS):
            cx = self.x_palette(i)
            if (x - cx) ** 2 + (y - Y_PALETTE) ** 2 <= R_PALETTE ** 2:
                return c
        return None

    def clic(self, event):
        c = self.couleur_sous(event.x, event.y)
        if c:
            # On prend un pion dans la palette : il suit la souris
            self.couleur_choisie = c
            self.dessiner()
            self.pion_glisse = self.canvas.create_oval(
                event.x - R_TROU, event.y - R_TROU, event.x + R_TROU, event.y + R_TROU,
                fill=TEINTES[c], outline="white", width=2)
            return
        trou = self.trou_sous(event.x, event.y)
        if trou is not None and self.couleur_choisie:
            # Clic sur un trou avec une couleur déjà choisie
            self.proposition[trou] = self.couleur_choisie
            self.dessiner()

    def glisser(self, event):
        if self.pion_glisse:
            self.canvas.coords(self.pion_glisse, event.x - R_TROU, event.y - R_TROU,
                               event.x + R_TROU, event.y + R_TROU)

    def relacher(self, event):
        if self.pion_glisse:
            self.canvas.delete(self.pion_glisse)
            self.pion_glisse = None
            trou = self.trou_sous(event.x, event.y)
            if trou is not None:
                self.proposition[trou] = self.couleur_choisie
                self.dessiner()

    def clic_droit(self, event):
        # Clic droit sur un pion de la ligne en cours : on le retire
        trou = self.trou_sous(event.x, event.y)
        if trou is not None:
            self.proposition[trou] = None
            self.dessiner()

    # ---------- Dessin ----------

    def y_ligne(self, n):
        return Y_PLATEAU + n * LIGNE_H + LIGNE_H // 2

    def x_palette(self, i):
        return 55 + i * 62

    def pion(self, x, y, r, couleur, contour="black"):
        if couleur:
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=TEINTES[couleur],
                                    outline=contour, width=2)
            # petit reflet pour faire "pion"
            self.canvas.create_oval(x - r * 0.55, y - r * 0.6, x - r * 0.1, y - r * 0.2,
                                    fill="white", outline="", stipple="gray50")
        else:
            self.canvas.create_oval(x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45,
                                    fill=TROU, outline="")

    def dessiner(self):
        cv = self.canvas
        cv.delete("all")

        cv.create_text(LARGEUR // 2, 25, text="BenjiMind", fill="white", font=("Arial", 20, "bold"))

        # Code secret (caché tant que la partie n'est pas finie)
        cv.create_rectangle(40, Y_SECRET - 25, X_TROUS + (LONGUEUR - 1) * ECART_TROUS + 40,
                            Y_SECRET + 25, fill=TROU, outline="")
        for i in range(LONGUEUR):
            x = X_TROUS + i * ECART_TROUS
            if self.fini:
                self.pion(x, Y_SECRET, R_TROU, self.code[i])
            else:
                cv.create_oval(x - R_TROU, Y_SECRET - R_TROU, x + R_TROU, Y_SECRET + R_TROU,
                               fill="#9e9e9e", outline="")
                cv.create_text(x, Y_SECRET, text="?", fill="white", font=("Arial", 14, "bold"))
        cv.create_text(X_INDICES + 30, Y_SECRET - 8, text="● bien placé", fill="#ff5252",
                       font=("Arial", 9, "bold"))
        cv.create_text(X_INDICES + 30, Y_SECRET + 10, text="● mal placé", fill="white",
                       font=("Arial", 9, "bold"))

        # Lignes d'essai
        for n in range(ESSAIS_MAX):
            y = self.y_ligne(n)
            if n == self.essai and not self.fini:
                cv.create_rectangle(10, y - LIGNE_H // 2 + 2, LARGEUR - 10, y + LIGNE_H // 2 - 2,
                                    fill=SURBRILLANCE, outline="white")
            cv.create_text(30, y, text=str(n + 1), fill="white", font=("Arial", 11, "bold"))

            if n < len(self.historique):
                prop, bien, mal = self.historique[n]
                couleurs = list(prop)
            elif n == self.essai and not self.fini:
                couleurs = self.proposition
                bien, mal = None, None
            else:
                couleurs = [None] * LONGUEUR
                bien, mal = None, None

            for i in range(LONGUEUR):
                self.pion(X_TROUS + i * ECART_TROUS, y, R_TROU, couleurs[i])

            # Petits pions d'indice en carré 2x2
            indices = []
            if bien is not None:
                indices = ["#ff1744"] * bien + ["white"] * mal
            for k in range(LONGUEUR):
                ix = X_INDICES + (k % 2) * 16
                iy = y - 8 + (k // 2) * 16
                if k < len(indices):
                    cv.create_oval(ix - 6, iy - 6, ix + 6, iy + 6, fill=indices[k], outline="black")
                else:
                    cv.create_oval(ix - 3, iy - 3, ix + 3, iy + 3, fill=TROU, outline="")

        # Palette de couleurs
        cv.create_text(LARGEUR // 2, Y_PALETTE - 30,
                       text="Glissez ou cliquez une couleur puis un trou  —  clic droit : retirer",
                       fill="white", font=("Arial", 9))
        for i, c in enumerate(COULEURS):
            x = self.x_palette(i)
            contour = "white" if c == self.couleur_choisie else "black"
            self.pion(x, Y_PALETTE, R_PALETTE, c, contour)
            if c == self.couleur_choisie:
                cv.create_oval(x - R_PALETTE - 4, Y_PALETTE - R_PALETTE - 4,
                               x + R_PALETTE + 4, Y_PALETTE + R_PALETTE + 4,
                               outline="white", width=2)

        # Le bouton Valider n'est actif que si la ligne est complète
        if self.fini or None in self.proposition:
            self.bouton_valider.config(state="disabled")
        else:
            self.bouton_valider.config(state="normal")


def main():
    fenetre = tk.Tk()
    fenetre.title("BenjiMind")
    fenetre.configure(bg=FOND)

    # Écran d'accueil : on demande le nom dans la fenêtre principale
    accueil = tk.Frame(fenetre, bg=FOND, padx=40, pady=30)
    accueil.pack()
    tk.Label(accueil, text="BenjiMind", fg="white", bg=FOND, font=("Arial", 22, "bold")).pack(pady=10)
    tk.Label(accueil, text="Entrez votre nom :", fg="white", bg=FOND, font=("Arial", 12)).pack()
    champ = tk.Entry(accueil, font=("Arial", 12), justify="center")
    champ.pack(pady=10)
    champ.focus_set()

    def commencer(event=None):
        nom = champ.get().strip() or "Joueur"
        accueil.destroy()
        Mastermind(fenetre, nom)

    tk.Button(accueil, text="Jouer", font=("Arial", 12, "bold"), width=10, command=commencer).pack()
    champ.bind("<Return>", commencer)

    # Force la fenêtre au premier plan (sinon elle peut s'ouvrir derrière VS Code)
    fenetre.lift()
    fenetre.attributes("-topmost", True)
    fenetre.after(300, lambda: fenetre.attributes("-topmost", False))
    fenetre.focus_force()

    fenetre.mainloop()


main()
