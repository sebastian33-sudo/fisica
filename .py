import pygame
import math
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
ANCHO, ALTO = 800, 600 # Tamaño de la ventana
FPS = 60 # Frames por segundo
K_COULOMB = 100000 # Constante de Coulomb ajustada para la simulación
DT = 0.1 # Paso de tiempo para la integración

# Colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
ROJO = (255, 50, 50)
AZUL = (50, 50, 255)
VERDE = (0, 255, 0)
GRIS = (100, 100, 100)

class CargaFija:
    def _init_(self, x, y, carga):
        self.x = x
        self.y = y
        self.carga = carga
        self.color = ROJO if carga > 0 else AZUL

    def dibujar(self, pantalla):
        pygame.draw.circle(pantalla, self.color, (int(self.x), int(self.y)), 15)
        font = pygame.font.SysFont('Arial', 20)
        texto = "+" if self.carga > 0 else "-"
        img = font.render(texto, True, BLANCO)
        pantalla.blit(img, (self.x - 5, self.y - 12))

class ParticulaMovil:
    def _init_(self, x, y, carga, masa):
        self.x = x
        self.y = y
        self.vx = 0 
        self.vy = 0 
        self.carga = carga
        self.masa = masa
        self.historial_x = [] 
        self.historial_y = []
        self.historial_fuerza = [] 

    def actualizar(self, fuerzas_x, fuerzas_y):
        # F = m * a
        ax = fuerzas_x / self.masa
        ay = fuerzas_y / self.masa

        # Integración
        self.vx += ax * DT
        self.vy += ay * DT

        # --- FRICCIÓN (Solución al problema de inestabilidad) ---
        self.vx *= 0.96  # Frena un 4% cada frame (resistencia del aire)
        self.vy *= 0.96  
        # -------------------------------------------------------

        self.x += self.vx * DT # Actualizar posición
        self.y += self.vy * DT 

        # Guardar datos
        self.historial_x.append(self.x)
        self.historial_y.append(self.y)
        fuerza_total = math.sqrt(fuerzas_x*2 + fuerzas_y*2)
        self.historial_fuerza.append(fuerza_total)

    def dibujar(self, pantalla):
        pygame.draw.circle(pantalla, VERDE, (int(self.x), int(self.y)), 8)

def main():
    # 1. Iniciar Pygame PRIMERO para poder detectar la pantalla
    pygame.init()

    # 2. Detectar el tamaño del monitor del usuario
    info_pantalla = pygame.display.Info()
    ANCHO = info_pantalla.current_w
    ALTO = info_pantalla.current_h

    # 3. Crear la ventana en modo FULLSCREEN
    pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.FULLSCREEN)
    
    pygame.display.set_caption("Simulador Electrostático Interactivo")
    reloj = pygame.time.Clock()
    font_instrucciones = pygame.font.SysFont('Arial', 16)

    # --- LISTAS VACÍAS AL INICIO ---
    cargas_fijas = []
    particula = None 

    ejecutando = True
    while ejecutando:
        pantalla.fill(NEGRO)

        # --- MANEJO DE EVENTOS ---
        for evento in pygame.event.get():
            # Permitir cerrar con la X o con la tecla ESCAPE (Importante en Fullscreen)
            if evento.type == pygame.QUIT:
                ejecutando = False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False
            
            # Detectar Clicks del Mouse
            if evento.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                if evento.button == 1: # Click Izquierdo
                    cargas_fijas.append(CargaFija(mx, my, 50))
                
                elif evento.button == 3: # Click Derecho
                    cargas_fijas.append(CargaFija(mx, my, -50))

            # Detectar Teclado (Lanzar y Reiniciar)
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    mx, my = pygame.mouse.get_pos()
                    particula = ParticulaMovil(mx, my, 10, 5.0)
                
                if evento.key == pygame.K_r:
                    cargas_fijas = []
                    particula = None

        # --- FÍSICA ---
        if particula is not None:
            fx_total = 0
            fy_total = 0

            for carga in cargas_fijas:
                dx = particula.x - carga.x
                dy = particula.y - carga.y
                distancia = math.sqrt(dx*2 + dy*2)

                if distancia < 10: distancia = 10 

                magnitud = K_COULOMB * abs(carga.carga * particula.carga) / (distancia**2)
                angulo = math.atan2(dy, dx)

                if (carga.carga * particula.carga) > 0: 
                    fx = magnitud * math.cos(angulo)
                    fy = magnitud * math.sin(angulo)
                else: 
                    fx = -magnitud * math.cos(angulo)
                    fy = -magnitud * math.sin(angulo)

                fx_total += fx
                fy_total += fy

            particula.actualizar(fx_total, fy_total)
            particula.dibujar(pantalla)
            
            # Dibujar vector fuerza
            pygame.draw.line(pantalla, (255, 255, 0), 
                             (particula.x, particula.y), 
                             (particula.x + fx_total, particula.y + fy_total), 2)

        # --- DIBUJAR ---
        for carga in cargas_fijas:
            carga.dibujar(pantalla)

        # Instrucciones (Ajustadas para que siempre salgan abajo a la izquierda)
        texto = "Click Izq: +Carga | Click Der: -Carga | Espacio: Lanzar | R: Reiniciar | ESC: Salir"
        img_texto = font_instrucciones.render(texto, True, GRIS)
        pantalla.blit(img_texto, (10, ALTO - 40)) # Usamos la variable ALTO detectada

        pygame.display.flip()
        reloj.tick(FPS)

    pygame.quit()

    # --- GRÁFICAS (Solo si hubo simulación) ---
    if particula and len(particula.historial_x) > 1:
        print("Generando gráficas...")
        
        plt.figure(figsize=(10, 5))  # Crear figura con tamaño adecuado
        
        # Gráfica 1
        plt.subplot(1, 2, 1)
        plt.title("Trayectoria")
        plt.plot(particula.historial_x, particula.historial_y, 'g-', label="Camino")
        for c in cargas_fijas:
            plt.plot(c.x, c.y, 'ro' if c.carga > 0 else 'bo')
        plt.gca().invert_yaxis() # Para coincidir con coordenadas de pantalla
        plt.grid()
        plt.legend()

        # Gráfica 2
        plt.subplot(1, 2, 2)
        plt.title("Fuerza Neta vs Tiempo")
        plt.plot(particula.historial_fuerza, 'orange')
        plt.ylabel("Newtons (Escalado)")
        plt.grid()

        plt.show()
    else:
        print("No se generaron datos suficientes para graficar.")

if _name_ == "_main_":
    main()