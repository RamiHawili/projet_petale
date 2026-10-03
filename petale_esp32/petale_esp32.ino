// Projet Pétale — ESP32 : piston (servo 180°) + ruban LED WS2812
// Commandes reçues par USB :
//   POS:90             -> le piston va à l'angle 90°
//   MONTER / DESCENDRE -> monte / descend pendant DUREE_MOUVEMENT_MS
//   MONTER:2000        -> idem pendant 2000 ms
//   STOP               -> arrêt immédiat du piston
// LED : pulsation permanente qui suit la hauteur du piston.
//   Piston bas  -> miel, faible, lent
//   Mi-hauteur  -> bois d'acacia
//   Piston haut -> caramel foncé, intense, rapide

#include <ESP32Servo.h>
#include <Adafruit_NeoPixel.h>

// --- Réglages piston ------------------------------------------------------------
const int PIN_SERVO    = 18;
const int ANGLE_BAS    = 0;     // limite basse du piston (sécurité)
const int ANGLE_HAUT   = 180;   // limite haute du piston (sécurité)
const int DELAI_PAS_MS = 8;                    // vitesse : pause entre chaque degré
const unsigned long DUREE_MOUVEMENT_MS = 1000;  // durée par défaut de MONTER/DESCENDRE

// --- Réglages LED ---------------------------------------------------------------
const int PIN_LED = 4;          // broche DIN du ruban
const int NB_LEDS = 45;         // nombre de LED allumées

// Limite de consommation du ruban (mA) : la luminosité baisse automatiquement au-delà
//   USB du PC seul          -> 400
//   alimentation 5V 2 A     -> 1500
//   alimentation 5V 5 A     -> 4000
const float LIMITE_MA = 400;
const float MA_PAR_CANAL = 20;  // consommation d'une couleur de LED à 255

// Couleurs (R, V, B) : bas -> milieu -> haut
const float MIEL[3]    = {90, 35, 2};      // miel ambré (piston bas)
const float BOIS[3]    = {55, 17, 1};      // bois / sève brune (mi-hauteur)
const float CARAMEL[3] = {30, 7, 0};       // marron très foncé, écorce (piston haut)

// Intensité au sommet de la pulsation (0-255)
const float LUM_PIC_BAS  = 70;    // piston en bas : faible
const float LUM_PIC_HAUT = 255;   // piston en haut : maximum
const float CREUX = 0.05;         // au creux de la pulsation : 5 % de l'intensité du pic
const float GAMMA = 2.0;          // correction de luminosité (rendu naturel pour l'œil)

// Durée d'une pulsation complète (ms)
const float PERIODE_BAS_MS  = 3000.0;  // piston en bas : lent
const float PERIODE_HAUT_MS = 250.0;   // piston en haut : rapide

const int RAFRAICH_LED_MS = 10;        // mise à jour du ruban toutes les 10 ms (fluide)

// --- État piston ------------------------------------------------------------------
Servo servo;
int angleActuel = ANGLE_BAS;
int angleCible  = ANGLE_BAS;
bool enMouvement = false;
unsigned long finMouvement = 0;
unsigned long dernierPas = 0;

// --- État LED -----------------------------------------------------------------------
Adafruit_NeoPixel ruban(NB_LEDS, PIN_LED, NEO_GRB + NEO_KHZ800);
float phase = 0.0;                 // avancement dans la pulsation (0 -> 1)
unsigned long dernierRafraich = 0;
uint32_t derniereCouleur = 0xFFFFFFFF;

String tampon = "";

// ================================ LED ================================

// Mélange deux valeurs : t = 0 -> a, t = 1 -> b
float melange(float a, float b, float t) {
  return a + (b - a) * t;
}

// Couleur selon la hauteur h (0 -> 1) : miel -> bois d'acacia -> caramel foncé
float teinte(int canal, float h) {
  if (h < 0.5) return melange(MIEL[canal], BOIS[canal], h * 2.0);
  return melange(BOIS[canal], CARAMEL[canal], (h - 0.5) * 2.0);
}

// Pulsation permanente dont couleur, intensité et vitesse suivent la hauteur du piston
void gererLeds() {
  unsigned long maintenant = millis();
  unsigned long ecoule = maintenant - dernierRafraich;
  if (ecoule < RAFRAICH_LED_MS) return;
  dernierRafraich = maintenant;

  // Hauteur du piston : 0 = tout en bas, 1 = tout en haut
  float h = (float)(angleActuel - ANGLE_BAS) / (float)(ANGLE_HAUT - ANGLE_BAS);
  h = constrain(h, 0.0, 1.0);

  // Vitesse : la phase avance plus vite quand le piston est haut
  float periode = melange(PERIODE_BAS_MS, PERIODE_HAUT_MS, h);
  phase += ecoule / periode;
  if (phase >= 1.0) phase -= (int)phase;

  // Forme de la pulsation : 0 -> 1 -> 0, douce (cosinus)
  float k = (1.0 - cos(2.0 * PI * phase)) / 2.0;

  // Intensité (0 -> 1), corrigée par le gamma sur l'intensité SEULE
  float pic = melange(LUM_PIC_BAS, LUM_PIC_HAUT, h) / 255.0;
  float lum = pow(pic * (CREUX + (1.0 - CREUX) * k), GAMMA);

  float r = teinte(0, h) * lum;
  float v = teinte(1, h) * lum;
  float b = teinte(2, h) * lum;

  // Limiteur de courant : réduit la luminosité si le ruban consommerait trop
  float courant = NB_LEDS * (r + v + b) * MA_PAR_CANAL / 255.0;
  if (courant > LIMITE_MA) {
    float facteur = LIMITE_MA / courant;
    r *= facteur;
    v *= facteur;
    b *= facteur;
  }

  uint32_t couleur = ruban.Color((uint8_t)r, (uint8_t)v, (uint8_t)b);
  if (couleur == derniereCouleur) return;   // rien à changer
  ruban.fill(couleur);
  ruban.show();
  derniereCouleur = couleur;
}

// ================================ PISTON ================================

void arreter(const char* raison) {
  enMouvement = false;
  Serial.printf("FIN (%s) : angle %d deg\n", raison, angleActuel);
}

void demarrer(int cible, unsigned long duree) {
  angleCible = constrain(cible, ANGLE_BAS, ANGLE_HAUT);
  finMouvement = millis() + duree;
  enMouvement = true;
}

void gererMouvement() {
  if (!enMouvement) return;
  if ((long)(millis() - finMouvement) >= 0) { arreter("duree"); return; }
  if (angleActuel == angleCible)            { arreter("position atteinte"); return; }
  if (millis() - dernierPas >= DELAI_PAS_MS) {
    angleActuel += (angleCible > angleActuel) ? 1 : -1;
    servo.write(angleActuel);
    dernierPas = millis();
  }
}

// ================================ COMMANDES ================================

void traiterMessage(String msg) {
  msg.trim();
  msg.toUpperCase();

  String commande = msg;
  String valeur = "";
  int deuxPoints = msg.indexOf(':');
  if (deuxPoints >= 0) {
    commande = msg.substring(0, deuxPoints);
    valeur = msg.substring(deuxPoints + 1);
  }
  unsigned long duree = (valeur.toInt() > 0) ? valeur.toInt() : DUREE_MOUVEMENT_MS;

  if (commande == "POS")            demarrer(valeur.toInt(), 60000);  // pas de limite de temps
  else if (commande == "MONTER")    demarrer(ANGLE_HAUT, duree);
  else if (commande == "DESCENDRE") demarrer(ANGLE_BAS, duree);
  else if (commande == "STOP")      { arreter("stop"); return; }
  else { Serial.println("ERR:" + msg); return; }

  Serial.printf("OK:%s -> cible %d deg\n", commande.c_str(), angleCible);
}

void lireSerie() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') { traiterMessage(tampon); tampon = ""; }
    else if (c != '\r') tampon += c;
  }
}

// ================================ PROGRAMME ================================

void setup() {
  Serial.begin(115200);
  delay(1500);

  ruban.begin();          // LED d'abord
  ruban.clear();
  ruban.show();

  servo.setPeriodHertz(50);
  servo.attach(PIN_SERVO, 400, 2500);
  servo.write(angleActuel);

  Serial.println("PRET");
}

void loop() {
  lireSerie();
  gererMouvement();
  gererLeds();
}