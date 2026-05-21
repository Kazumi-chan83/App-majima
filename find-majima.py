import os
import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.video import Video
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

import pygame
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
CANAL_BRUITAGE = pygame.mixer.Channel(1)

FAUX_PERSONNAGES = [
    'adachi.webp','akame.webp','akiyama.webp','chitose.webp','daigo.webp',
    'daisuke.webp','eric.webp','haruka.webp','hiroki.webp','ichiban.webp',
    'jo.webp','kaoru.webp','keiji.webp','kiryu.webp','kosei.webp',
    'masayohi.webp','mine.webp','nagumo.webp','nishikiyama.webp','noah.webp',
    'rikiya.webp','ryuji.webp','saeko.webp','shigeru.webp','taiga.webp',
    'yu nanba.webp'
]

DUREE_VIDEO      = 121.021   # secondes totales de la vidéo
BPM              = 144
DUREE_BEAT       = 60.0 / BPM          # 0.41666...s
MUSIC_OFFSET     = 2.2407              # secondes avant le 1er beat dans la vidéo


# ══════════════════════════════════════════════════════════════════════════════
# ÉCRAN SCORE
# ══════════════════════════════════════════════════════════════════════════════
class ScoreScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.05, 0.05, 0.05, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w,v: setattr(self._bg,'pos',v),
                  size=lambda w,v: setattr(self._bg,'size',v))

        layout = BoxLayout(orientation='vertical', padding=60, spacing=25)
        self.lbl_titre = Label(text="BAKA MITAI",  font_size='44sp', color=(1,1,0,1),  size_hint_y=0.15)
        self.lbl_score = Label(text="",             font_size='30sp', color=(1,1,1,1),  size_hint_y=0.45)
        self.lbl_grade = Label(text="",             font_size='72sp', bold=True,         size_hint_y=0.25)
        btn = Button(
            text="RETOUR AU MENU", font_size='24sp', size_hint_y=0.15,
            background_normal='', background_color=(0.15,0.05,0.05,1), color=(1,1,1,1)
        )
        btn.bind(on_release=lambda _: setattr(self.manager, 'current', 'menu'))
        for w in [self.lbl_titre, self.lbl_score, self.lbl_grade, btn]:
            layout.add_widget(w)
        self.add_widget(layout)

    def afficher(self, perfect, good, miss, total):
        score = perfect * 300 + good * 100
        self.lbl_score.text = (
            f"PERFECT  :  {perfect}\n"
            f"GOOD     :  {good}\n"
            f"MISS     :  {miss}\n"
            f"--------------------\n"
            f"SCORE    :  {score}"
        )
        pct = (perfect + good) / max(total, 1)
        if   pct >= 0.95: self.lbl_grade.text, self.lbl_grade.color = "S  ★",       (1,   0.9, 0,   1)
        elif pct >= 0.80: self.lbl_grade.text, self.lbl_grade.color = "A",           (0.3, 1,   0.4, 1)
        elif pct >= 0.60: self.lbl_grade.text, self.lbl_grade.color = "B",           (0.4, 0.8, 1,   1)
        elif pct >= 0.40: self.lbl_grade.text, self.lbl_grade.color = "C",           (1,   0.6, 0,   1)
        else:             self.lbl_grade.text, self.lbl_grade.color = "D  BAKA...",  (1,   0.2, 0.2, 1)


# ══════════════════════════════════════════════════════════════════════════════
# MENU
# ══════════════════════════════════════════════════════════════════════════════
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        layout.add_widget(Label(
            text="WHERE IS MAJIMA", font_size='36sp', color=(1,0,0,1), size_hint_y=0.25
        ))
        boutons = [
            ("FACILE  -  JEUNE JONIN",        "facile"),
            ("MOYEN",                           "moyen"),
            ("DIFFICILE  -  DRAGON DE DOJIMA", "difficile"),
            ("KARAOKE : BAKA MITAI",           "everywhere"),
        ]
        for texte, diff in boutons:
            btn = Button(
                text=texte, font_size='22sp',
                background_normal='', background_color=(0.1,0.1,0.1,1),
                color=(1,0,0,1) if diff == "everywhere" else (1,1,1,1)
            )
            btn.bind(on_release=lambda inst, d=diff: self.lancer_jeu(d))
            layout.add_widget(btn)
        self.add_widget(layout)

    def on_enter(self):
        try:
            pygame.mixer.music.load("Menu.wav")
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(loops=-1, fade_ms=500)
        except Exception as e:
            print(f"ERREUR AUDIO MENU : {e}")

    def lancer_jeu(self, diff):
        self.manager.get_screen('jeu').difficulte = diff
        self.manager.current = 'jeu'


# ══════════════════════════════════════════════════════════════════════════════
# TÊTE DS REBONDISSANTE
# ══════════════════════════════════════════════════════════════════════════════
class TeteSelectionnable(ButtonBehavior, Image):
    def __init__(self, est_majima=False, jeu=None, **kwargs):
        super().__init__(**kwargs)
        self.est_majima    = est_majima
        self.jeu           = jeu
        self.allow_stretch = True
        self.keep_ratio    = True
        self.size_hint     = (None, None)
        self.size          = (130, 130)
        v = {"facile":90,"moyen":170,"difficile":280}.get(
            jeu.difficulte if jeu else "moyen", 170)
        self.vx = random.uniform(v*0.6, v) * random.choice([-1,1])
        self.vy = random.uniform(v*0.6, v) * random.choice([-1,1])

    def bouger(self, dt, w, h):
        self.x += self.vx * dt;  self.y += self.vy * dt
        if self.x <= 0:               self.x = 0;            self.vx =  abs(self.vx)
        if self.x + self.width  >= w: self.x = w-self.width; self.vx = -abs(self.vx)
        if self.y <= 0:               self.y = 0;            self.vy =  abs(self.vy)
        if self.y + self.height >= h: self.y = h-self.height;self.vy = -abs(self.vy)

    def on_press(self):
        if self.est_majima:
            self.jeu.titre.text  = "KIRYU CHAN !!!"
            self.jeu.titre.color = (0,1,0,1)
            try: CANAL_BRUITAGE.play(pygame.mixer.Sound("kiryu.wav"))
            except: pass
            Clock.schedule_once(lambda dt: self.jeu.recharger_tetes(), 1.5)
        else:
            self.jeu.titre.text  = "CE N'EST PAS LUI !"
            self.jeu.titre.color = (1,0.4,0,1)


# ══════════════════════════════════════════════════════════════════════════════
# FLÈCHE KARAOKÉ
# Texte ASCII pur — visible sur toutes les polices Windows
# ══════════════════════════════════════════════════════════════════════════════
TEXTE_FLECHE = {"GAUCHE": "<--", "DROITE": "-->", "HAUT": " ^ ", "BAS":  " v "}
COULEURS_FLECHE = {
    "GAUCHE":  (0.3, 0.7, 1,   1),   # bleu
    "DROITE":  (1,   0.35,0.35,1),   # rouge
    "HAUT":    (0.3, 1,   0.3, 1),   # vert
    "BAS":     (1,   0.9, 0.1, 1),   # jaune
}

class FlecheKaraoke(Label):
    def __init__(self, type_fleche, vitesse, temps_target, cy, **kwargs):
        super().__init__(**kwargs)
        self.type_fleche  = type_fleche
        self.vitesse      = vitesse
        self.temps_target = temps_target
        self.text         = TEXTE_FLECHE[type_fleche]
        self.font_size    = '54sp'
        self.bold         = True
        self.color        = COULEURS_FLECHE[type_fleche]
        self.size_hint    = (None, None)
        self.size         = (120, 80)
        self.x            = Window.width + 20
        self.y            = cy


# ══════════════════════════════════════════════════════════════════════════════
# ÉCRAN DE JEU
# ══════════════════════════════════════════════════════════════════════════════
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.difficulte          = "moyen"
        self.evenement_jeu       = None
        self.fleches_actives     = []
        self.tetes_ds            = []
        self.prochain_beat_index = 0
        self.vitesse_defilement  = 380
        self.cible_x             = 160
        self.nb_perfect = self.nb_good = self.nb_miss = self.nb_total = 0
        self.video_widget        = None
        self.cy                  = 0

        self.layout_principal = BoxLayout(orientation='vertical')

        barre = BoxLayout(orientation='horizontal', size_hint_y=None, height=55,
                          padding=(8,4), spacing=8)
        with barre.canvas.before:
            Color(0.08,0.08,0.08,1)
            self._bg = Rectangle(pos=barre.pos, size=barre.size)
        barre.bind(pos=lambda w,v: setattr(self._bg,'pos',v),
                   size=lambda w,v: setattr(self._bg,'size',v))

        self.titre = Label(text="FIND MAJIMA", font_size='26sp', color=(1,0,0,1))
        btn_retour = Button(
            text="RETOUR", size_hint_x=None, width=110, font_size='18sp',
            background_normal='', background_color=(0.25,0.05,0.05,1), color=(1,1,1,1)
        )
        btn_retour.bind(on_release=self.retour_menu)
        barre.add_widget(self.titre)
        barre.add_widget(btn_retour)
        self.layout_principal.add_widget(barre)

        self.zone_contenu = FloatLayout()
        self.layout_principal.add_widget(self.zone_contenu)
        self.add_widget(self.layout_principal)

    def on_enter(self):
        self.generer_partie()

    # ─────────────────────────────────────────────────────────────────────────
    def generer_partie(self):
        self.stopper_jeu()
        self.zone_contenu.clear_widgets()
        self.fleches_actives     = []
        self.tetes_ds            = []
        self.prochain_beat_index = 0
        self.nb_perfect = self.nb_good = self.nb_miss = self.nb_total = 0
        self.video_widget        = None

        # ══ KARAOKÉ ═══════════════════════════════════════════════════════════
        if self.difficulte == "everywhere":
            self.titre.text  = "BAKA MITAI"
            self.titre.color = (1,1,0,1)

            # Vidéo en fond — volume=0, le son vient de pygame
            if os.path.exists("Bakamitai.mp4"):
                self.video_widget = Video(
                    source="Bakamitai.mp4", state="play",
                    allow_stretch=True, keep_ratio=False,
                    size_hint=(1,1), pos_hint={"x":0,"y":0},
                    volume=0, options={"eos":"stop"}
                )
                self.zone_contenu.add_widget(self.video_widget)

            # Overlay sombre
            ov = Label(text="", size_hint=(1,1), pos_hint={"x":0,"y":0})
            with ov.canvas.before:
                Color(0,0,0,0.45)
                self._ov_rect = Rectangle(pos=ov.pos, size=ov.size)
            ov.bind(pos=lambda w,v: setattr(self._ov_rect,'pos',v),
                    size=lambda w,v: setattr(self._ov_rect,'size',v))
            self.zone_contenu.add_widget(ov)

            # Rail de jeu centré verticalement
            self.cy = Window.height // 2 - 40

            self.label_rail = Label(
                text="- - - - - - - - - - - - - - - - - - - - - - - - - - - -",
                font_size='18sp', color=(1,1,1,0.18),
                size_hint=(1,None), height=30,
                pos_hint={"x":0}, y=self.cy + 25
            )
            self.zone_contenu.add_widget(self.label_rail)

            # Cible fixe
            self.visuel_cible = Label(
                text="[X]", font_size='52sp', bold=True, color=(1,1,1,0.85),
                size_hint=(None,None), size=(100,80),
                x=self.cible_x - 50, y=self.cy
            )
            self.zone_contenu.add_widget(self.visuel_cible)

            # HUD
            self.hud = Label(
                text="PERFECT: 0   GOOD: 0   MISS: 0",
                font_size='20sp', color=(1,1,1,1),
                size_hint=(None,None), size=(520,35),
                x=10, y=Window.height - 95
            )
            self.zone_contenu.add_widget(self.hud)

            # Feedback frappe
            self.label_feedback = Label(
                text="", font_size='46sp', bold=True,
                size_hint=(None,None), size=(440,70),
                x=Window.width//2 - 220,
                y=Window.height//2 + 80, color=(1,1,1,1)
            )
            self.zone_contenu.add_widget(self.label_feedback)

            # Audio pygame — démarre en même temps que la vidéo
            # On démarre à t=0 dans l'audio, les beats commencent à MUSIC_OFFSET
            try:
                pygame.mixer.music.load("Bakamitai_audio.wav")
                pygame.mixer.music.set_volume(0.9)
                pygame.mixer.music.play(loops=0)
            except Exception as e:
                print(f"ERREUR AUDIO : {e}")

            Window.bind(on_key_down=self.touche_pressee)
            self.evenement_jeu = Clock.schedule_interval(self.update_karaoke, 1/60.0)

        # ══ MODE DS ═══════════════════════════════════════════════════════════
        else:
            self.titre.color = (1,0,0,1)
            try:
                pygame.mixer.music.load("Game.wav")
                pygame.mixer.music.set_volume(0.2)
                pygame.mixer.music.play(loops=-1)
            except: pass

            nb   = {"facile":8,"moyen":16,"difficile":24}.get(self.difficulte,16)
            noms = {"facile":"FACILE - JEUNE JONIN","moyen":"MOYEN","difficile":"DRAGON DE DOJIMA"}
            self.titre.text = noms.get(self.difficulte,"MOYEN")

            visages = random.choices(FAUX_PERSONNAGES, k=nb-1)
            cases   = [TeteSelectionnable(source=img, est_majima=False, jeu=self) for img in visages]
            cases.append(TeteSelectionnable(source="majima.webp", est_majima=True, jeu=self))
            random.shuffle(cases)

            self.tetes_ds = cases
            for t in cases:
                t.pos = (
                    random.randint(0, max(10, int(Window.width)-130)),
                    random.randint(0, max(10, int(Window.height)-130)),
                )
                self.zone_contenu.add_widget(t)
            self.evenement_jeu = Clock.schedule_interval(self.update_ds, 1/60.0)


    # ─────────────────────────────────────────────────────────────────────────
    # RECHARGE LES TETES SANS TOUCHER A LA MUSIQUE
    # ─────────────────────────────────────────────────────────────────────────
    def recharger_tetes(self):
        if self.evenement_jeu:
            Clock.unschedule(self.evenement_jeu)
            self.evenement_jeu = None
        self.zone_contenu.clear_widgets()
        self.tetes_ds = []
        nb   = {"facile":8,"moyen":16,"difficile":24}.get(self.difficulte,16)
        noms = {"facile":"FACILE - JEUNE JONIN","moyen":"MOYEN","difficile":"DRAGON DE DOJIMA"}
        self.titre.text  = noms.get(self.difficulte,"MOYEN")
        self.titre.color = (1,0,0,1)
        visages = random.choices(FAUX_PERSONNAGES, k=nb-1)
        cases   = [TeteSelectionnable(source=img, est_majima=False, jeu=self) for img in visages]
        cases.append(TeteSelectionnable(source="majima.webp", est_majima=True, jeu=self))
        random.shuffle(cases)
        self.tetes_ds = cases
        for t in cases:
            t.pos = (
                random.randint(0, max(10, int(Window.width)-130)),
                random.randint(0, max(10, int(Window.height)-130)),
            )
            self.zone_contenu.add_widget(t)
        self.evenement_jeu = Clock.schedule_interval(self.update_ds, 1/60.0)

    # ─────────────────────────────────────────────────────────────────────────
    # UPDATE DS
    # ─────────────────────────────────────────────────────────────────────────
    def update_ds(self, dt):
        w = self.zone_contenu.width
        h = self.zone_contenu.height
        for t in self.tetes_ds:
            t.bouger(dt, w, h)

    # ─────────────────────────────────────────────────────────────────────────
    # UPDATE KARAOKÉ — synchronisation sur get_pos() de pygame
    # Les beats sont calés sur MUSIC_OFFSET : beat N arrive à MUSIC_OFFSET + N*DUREE_BEAT
    # ─────────────────────────────────────────────────────────────────────────
    def update_karaoke(self, dt):
        temps_actuel = pygame.mixer.music.get_pos() / 1000.0  # position réelle audio

        # Fin de morceau → écran score
        if temps_actuel > 2.0 and not pygame.mixer.music.get_busy():
            self.fin_karaoke()
            return

        # Temps musical (relatif aux beats) : on soustrait l'offset
        temps_musical = temps_actuel - MUSIC_OFFSET

        # Spawn des flèches avec anticipation
        temps_anticipation  = (Window.width - self.cible_x) / self.vitesse_defilement
        temps_prochain_beat = self.prochain_beat_index * DUREE_BEAT

        while temps_musical + temps_anticipation >= temps_prochain_beat:
            # temps absolu dans l'audio où ce beat doit être frappé
            temps_abs_beat = MUSIC_OFFSET + temps_prochain_beat
            if temps_abs_beat <= DUREE_VIDEO:
                type_f = random.choice(["GAUCHE","HAUT","BAS","DROITE"])
                f = FlecheKaraoke(
                    type_fleche=type_f,
                    vitesse=self.vitesse_defilement,
                    temps_target=temps_abs_beat,   # en secondes absolues audio
                    cy=self.cy
                )
                self.zone_contenu.add_widget(f)
                self.fleches_actives.append(f)
                self.nb_total += 1
            self.prochain_beat_index += 1
            temps_prochain_beat = self.prochain_beat_index * DUREE_BEAT

        # Déplacement flèches : position X = f(temps restant avant le beat)
        for fleche in list(self.fleches_actives):
            temps_restant = fleche.temps_target - temps_actuel
            fleche.x = self.cible_x + (temps_restant * self.vitesse_defilement)

            if temps_actuel - fleche.temps_target > 0.28:
                self.nb_miss += 1
                self._feedback("MISS !!", (1,0.2,0.2,1))
                self.zone_contenu.remove_widget(fleche)
                self.fleches_actives.remove(fleche)
                self._maj_hud()

    # ─────────────────────────────────────────────────────────────────────────
    # INPUT
    # ─────────────────────────────────────────────────────────────────────────
    def touche_pressee(self, window, key, scancode, codepoint, modifier):
        touches = {276:"GAUCHE", 273:"HAUT", 274:"BAS", 275:"DROITE"}
        if key not in touches:
            return True
        attendue     = touches[key]
        temps_actuel = pygame.mixer.music.get_pos() / 1000.0

        meilleure, meilleur_ecart = None, 9999
        for f in self.fleches_actives:
            e = abs(temps_actuel - f.temps_target)
            if e < 0.20 and e < meilleur_ecart:
                meilleure, meilleur_ecart = f, e

        if meilleure:
            if meilleure.type_fleche == attendue:
                if meilleur_ecart <= 0.07:
                    self.nb_perfect += 1;  self._feedback("PERFECT !!", (0.3,1,0.3,1))
                else:
                    self.nb_good    += 1;  self._feedback("GOOD !",     (1,0.9,0.1,1))
            else:
                self.nb_miss += 1;         self._feedback("BAD TYPE !", (1,0.2,0.2,1))
            self.zone_contenu.remove_widget(meilleure)
            self.fleches_actives.remove(meilleure)
            self._maj_hud()
        return True

    def _feedback(self, texte, couleur):
        self.label_feedback.text  = texte
        self.label_feedback.color = couleur
        Clock.unschedule(self._effacer_feedback)
        Clock.schedule_once(self._effacer_feedback, 0.55)

    def _effacer_feedback(self, dt):
        self.label_feedback.text = ""

    def _maj_hud(self):
        self.hud.text = f"PERFECT: {self.nb_perfect}   GOOD: {self.nb_good}   MISS: {self.nb_miss}"

    # ─────────────────────────────────────────────────────────────────────────
    # FIN
    # ─────────────────────────────────────────────────────────────────────────
    def fin_karaoke(self):
        self.stopper_jeu()
        s = self.manager.get_screen('score')
        s.afficher(self.nb_perfect, self.nb_good, self.nb_miss, self.nb_total)
        self.manager.current = 'score'

    def stopper_jeu(self):
        try: Window.unbind(on_key_down=self.touche_pressee)
        except: pass
        if self.evenement_jeu:
            Clock.unschedule(self.evenement_jeu)
            self.evenement_jeu = None
        pygame.mixer.music.stop()
        if self.video_widget:
            try: self.video_widget.state = "stop"
            except: pass
            self.video_widget = None

    def retour_menu(self, instance):
        self.stopper_jeu()
        self.zone_contenu.clear_widgets()
        self.manager.current = 'menu'


# ══════════════════════════════════════════════════════════════════════════════
class MainApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='jeu'))
        sm.add_widget(ScoreScreen(name='score'))
        return sm

if __name__ == '__main__':
    MainApp().run()