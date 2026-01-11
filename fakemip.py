import pygame
import random
import time
import sys
import math
import socket
import threading

# --- Configuration ---
WINDOW_WIDTH = 700 
WINDOW_HEIGHT = 600 
NORMAL_IMAGE_PATH = 'fakeMIP-normal.png' 
DANCE_IMAGE_PATH = 'fakeMIP-dancing.png' 

# Sound Categories
DANCE_SOUNDS = ['MiPDance_1.wav', 'MiPDance_2.wav'] 
IDLE_SOUNDS = ['MiP_yapping2self.wav', 'MiP_hahahamip.wav', 'MiP_yippee.wav', 'MiP_mip1.wav', 'MiP_mip3.wav']
STARTUP_SOUND = 'MiP_mipthenoh.wav'
POWER_DOWN_SOUND = 'MiP_powerdown.wav'
SAD_SOUNDS = ['MiP_ohno.wav', 'MiP_aww.wav']

# Networking Setup
UDP_PORT = 2014 
BROADCAST_IP = "255.255.255.255"

# --- HUMAN-READABLE IDENTITY ---
NAMES = ['Jarold', 'Carl', 'Timothy', 'Bartholomew', 'Garry', 'Sprocket', 'Rusty', 'Zippy', 'Timny', 'Jimny']
MY_NAME = f"MiP_{random.choice(NAMES)}_{random.randint(100, 999)}"

# Frequency Tweaks
CHANCE_TO_DANCE = 0.001 
DANCE_COOLDOWN_SECONDS = 30 

# Global flags for network communication
network_trigger = False
network_sad_trigger = False

def network_listener():
    """Listens for other MiPs dancing or leaving."""
    global network_trigger, network_sad_trigger
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', UDP_PORT))
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode()
            sender_name, command = message.split(":")
            
            if sender_name != MY_NAME:
                if command == "DANCE":
                    print(f"{MY_NAME} heard {sender_name} dancing! Joining in 1 second...")
                    time.sleep(1)
                    network_trigger = True
                elif command == "POWER_OFF":
                    print(f"{MY_NAME} heard {sender_name} leave. So sad...")
                    network_sad_trigger = True
        except:
            pass

def send_signal(command):
    """Broadcasts a command (DANCE or POWER_OFF)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"{MY_NAME}:{command}"
        sock.sendto(message.encode(), (BROADCAST_IP, UDP_PORT))
        sock.close()
    except:
        pass

def main():
    global network_trigger, network_sad_trigger
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"FakerMiP - {MY_NAME}") 

    threading.Thread(target=network_listener, daemon=True).start()

    try:
        raw_normal = pygame.image.load(NORMAL_IMAGE_PATH).convert_alpha()
        normal_img = pygame.transform.scale(raw_normal, (WINDOW_WIDTH, WINDOW_HEIGHT)) 
        raw_dance = pygame.image.load(DANCE_IMAGE_PATH).convert_alpha()
        base_dance_img = pygame.transform.scale(raw_dance, (WINDOW_WIDTH, WINDOW_HEIGHT)) 
        
        dance_sfx = [pygame.mixer.Sound(s) for s in DANCE_SOUNDS] 
        idle_sfx = [pygame.mixer.Sound(s) for s in IDLE_SOUNDS]
        startup_sfx = pygame.mixer.Sound(STARTUP_SOUND)
        powerdown_sfx = pygame.mixer.Sound(POWER_DOWN_SOUND)
        sad_sfx = [pygame.mixer.Sound(s) for s in SAD_SOUNDS]
    except pygame.error as e:
        print(f"Error loading files: {e}")
        return

    startup_sfx.play()
    running = True
    is_dancing = False
    clock = pygame.time.Clock()
    last_idle_time = time.time()
    next_idle_delay = random.uniform(1, 20)
    last_dance_finish_time = 0 

    try:
        while running:
            current_time = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not is_dancing:
                        is_dancing = True
                        send_signal("DANCE")

            # Respond to network dance
            if network_trigger and not is_dancing:
                is_dancing = True
                network_trigger = False

            # Respond to network departure (Aww...)
            if network_sad_trigger:
                if not pygame.mixer.get_busy():
                    random.choice(sad_sfx).play()
                    network_sad_trigger = False
                else:
                    # If already busy, just clear it so we don't queue up a bunch
                    network_sad_trigger = False

            if not is_dancing:
                screen.fill((0, 0, 0))
                idle_pitch = 1.0 + (math.sin(current_time * 2) * 0.02)
                idle_img = pygame.transform.scale(normal_img, (WINDOW_WIDTH, int(WINDOW_HEIGHT * idle_pitch)))
                idle_rect = idle_img.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
                screen.blit(idle_img, idle_rect.topleft)
                
                if current_time - last_idle_time > next_idle_delay:
                    if not pygame.mixer.get_busy():
                        random.choice(idle_sfx).play()
                        last_idle_time = current_time
                        next_idle_delay = random.uniform(1, 20)

                if current_time - last_dance_finish_time > DANCE_COOLDOWN_SECONDS:
                    if random.random() < CHANCE_TO_DANCE:
                        is_dancing = True
                        send_signal("DANCE")
            
            if is_dancing:
                network_trigger = False 
                selected_sound = random.choice(dance_sfx) 
                channel = selected_sound.play(loops=2) 
                start_time = time.time()
                
                while channel.get_busy():
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            channel.stop()
                            running = False
                            break
                    if not running: break
                    
                    t = (time.time() - start_time) * 8
                    w_factor = 0.9 + (math.sin(t) * 0.1) 
                    h_factor = 0.95 + (math.cos(t * 1.2) * 0.05)
                    roll = math.sin(t * 0.8) * 5 
                    scaled = pygame.transform.scale(base_dance_img, (int(WINDOW_WIDTH * w_factor), int(WINDOW_HEIGHT * h_factor)))
                    final = pygame.transform.rotate(scaled, roll)
                    rect = final.get_rect(center=(WINDOW_WIDTH//2 + (math.sin(t) * 15), WINDOW_HEIGHT//2))

                    screen.fill((0, 0, 0))
                    screen.blit(final, rect.topleft)
                    pygame.display.flip()
                    clock.tick(60)
                
                if running:
                    if random.random() < 0.3: random.choice(sad_sfx).play()
                    screen.fill((0, 0, 0))
                    screen.blit(normal_img, (0, 0))
                    pygame.display.flip()
                    time.sleep(2) 
                    last_dance_finish_time = time.time()
                    last_idle_time = time.time()
                    next_idle_delay = random.uniform(1, 20)
                    is_dancing = False

            pygame.display.flip()
            clock.tick(60) 

    except KeyboardInterrupt:
        pass 
    
    # Broadcast to friends that we are leaving
    send_signal("POWER_OFF")
    
    print("Powering down...")
    screen.fill((0, 0, 0)); screen.blit(normal_img, (0, 0)); pygame.display.flip()
    pd_channel = powerdown_sfx.play()
    while pd_channel.get_busy(): pygame.time.delay(100)
    pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()