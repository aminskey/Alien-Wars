import pygame, cv2
import random, math
import os, numpy as np
import json

from pygame.locals import *

gameTitle = "Alien Wars"

pygame.init()
screen = pygame.display.set_mode((900, 600), SCALED | FULLSCREEN)
#screen = pygame.display.set_mode((900, 600))
pygame.display.set_caption(gameTitle)

clock = pygame.time.Clock()
FPS = 60

playerGroup = pygame.sprite.Group()
cloudsGroup1 = pygame.sprite.Group()
cloudsGroup2 = pygame.sprite.Group()
allClouds = pygame.sprite.Group()
textGroup = pygame.sprite.Group()
fireGroup = pygame.sprite.Group()
healthBarGroup = pygame.sprite.Group()
sporeGroup = pygame.sprite.Group()
bgGroup = pygame.sprite.Group()
wingmanGroup = pygame.sprite.Group()
powerUpGroup = pygame.sprite.Group()
bossGroup = pygame.sprite.Group()
allSprites = pygame.sprite.Group()


sfxChannel = pygame.mixer.Channel(0)
bombSFX = pygame.mixer.Channel(1)
msgChannel = pygame.mixer.Channel(2)
explosionChannel = pygame.mixer.Channel(3)

pygame.mixer.set_num_channels(16)

pygame.mouse.set_visible(0)

debug = False

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREY = (100, 100, 100)
ORANGE = (250, 140, 0)

with open("files/gameData.json", "r") as f:
    gameData = json.load(f)
    f.close()
class Cloud(pygame.sprite.Sprite):
    def __init__(self, type="cloud", image=None):
        super().__init__()
        if image != None:
            self.image = pygame.image.load(f"levels/fgObjects/{image}.png")
        else:
            objects = os.listdir(f"levels/fgObjects/{type}")
            self.image = pygame.image.load(f"levels/fgObjects/{type}/{objects[random.randint(0, len(objects) - 1)]}")
        self.rect = self.image.get_rect()

        self.rect.midbottom = (random.randint(0, screen.get_width()), random.randint(-screen.get_height(), 0))
    def update(self, speed=2):
        self.rect.y += speed
        if self.rect.midtop[1] > screen.get_height():
            self.rect.y = -self.image.get_height()
            self.rect.x = random.randint(0, screen.get_width())


class Player(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__()

        playerData = gameData["players"][name]

        self.base_image = pygame.image.load(f"player/{name}/{name}.png")
        self.image = self.base_image

        self.name = name
        self.rect = self.image.get_rect()
        self.speed = playerData["speed"] if "speed" in playerData else 5
        self.points = 0

        self.left_img = pygame.image.load(f"player/{name}/{name}-left.png")
        self.right_img = pygame.image.load(f"player/{name}/{name}-right.png")

        self.bombImg = pygame.image.load("misc/bomb-icon.png")
        self.cooldown = 5
        self.health = 100
        self.maxHealth = 100
        self.lives = 3
        self.bombs = 5
        self.weaponType = playerData["weaponType"]
        self.damage = playerData["damage"]

        self.bombCooldown = 20
        self.bombSound = pygame.mixer.Sound("SFX/bomb_drop.wav")
        self.bombDown = False
        self.bombDamage = playerData["bombDamage"]

        self.levelIndex = 0

    def rectifyPos(self):
        if self.rect.midright[0] > screen.get_width() - 10:
            self.rect.x -= self.speed * 2
        if self.rect.midleft[0] < 10:
            self.rect.x += self.speed * 2

        if self.rect.midtop[1] < 0:
            self.rect.y += self.speed * 2
        if self.rect.midbottom[1] > screen.get_height() - 10:
            self.rect.y -= self.speed * 2
    def fire(self):
        tmp = Lazer(self.weaponType, damage=self.damage, mount_point=self.rect.midtop, sizeFactor=0.2, speed=15)
        tmp.sender = self
        tmp.oppGroup = sporeGroup
        fireGroup.add(tmp)
        allSprites.add(tmp)

    def move(self, key_read, ver_keys=[K_LEFT, K_RIGHT], hor_keys=[K_UP, K_DOWN]):
        if key_read[ver_keys[0]]:
            self.rect.x -= self.speed
            self.image = self.left_img
        if key_read[ver_keys[1]]:
            self.rect.x += self.speed
            self.image = self.right_img
        if key_read[hor_keys[0]]:
            self.rect.y -= self.speed
        if key_read[hor_keys[1]]:
            self.rect.y += self.speed

    def bombOnClick(self, inKeys, button=K_f):
        if inKeys[button]:
            if self.bombCooldown <= 0 and self.bombs > 0:
                # Play drop sound effect
                bombSFX.play(self.bombSound)

                # has bomb been thrown??
                self.bombDown = True

                # set bombCooldown to zero
                self.bombCooldown = 0
        # If bomb has been thrown, and the amount of frames gone is equal to the length in seconds*fps of the song. Explode!!!
        if self.bombCooldown < -self.bombSound.get_length()*FPS and self.bombDown:
            # decrease num of bombs
            self.bombs -= 1

            # We are not throwing any more bombs
            self.bombDown = False

            # Cooldown to prevent spam
            self.bombCooldown = 20

            pygame.mixer.Sound("SFX/ship-explosion.wav").play()

            # Decrease health of every spore, and destroy every lazer object
            for sprite in sporeGroup.sprites():
                if not isinstance(sprite, Explosion):
                    boom = Explosion(explosion, 1, 1, sprite.rect.center)
                    sporeGroup.add(boom)

                    # does the sprite have a health tag??
                    if hasattr(sprite, "health"):
                        # checking if the sprite is invincable or not
                        if not hasattr(sprite, "invincable"):
                            # if not then deal damage
                            sprite.health -= self.bombDamage
                        # is the sprite a coherent to a premature??
                        if hasattr(sprite, "premature"):
                            # if so then deal damage to main body.
                            sprite.premature.health -= self.bombDamage
                        # if the sprite dies, then increase the killers points.
                        if sprite.health <= 0:
                            self.points += sprite.points
            # kill all sprites in fireGroup (such as bombs and lazers)
            for sprite in fireGroup.sprites():
                sprite.kill()
        else:
            # if not, then decrease the cooldown further.
            self.bombCooldown -= 1

    def printLifeCount(self, window=screen):
        im_res = (self.base_image.get_width() // 1.2, self.base_image.get_height() // 1.2)
        image = pygame.transform.scale(self.base_image, im_res)
        for i in range(self.lives):
            window.blit(image,
                        (i * image.get_width(), window.get_height() - image.get_height()*2))
    def printBombCount(self, window=screen):
        for i in range(self.bombs):
            window.blit(self.bombImg, (i * self.bombImg.get_width(), 0))
    def update(self):
        keys = pygame.key.get_pressed()

        if keys[K_SPACE]:
            if self.cooldown <= 0:
                self.fire()
                self.cooldown = 5
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.bombCooldown > 0:
            self.bombCooldown -= 1

        self.bombOnClick(keys)

        if pygame.sprite.spritecollideany(self, sporeGroup):
            sprite = pygame.sprite.spritecollideany(self, sporeGroup)
            if not isinstance(sprite, Explosion):
                self.health = 0
                sprite.health -= 50

        if self.health <= 0:
            tmp = Explosion(explosion, 2, 1, self.rect.center, False, "SFX/ship-explosion.wav")
            playerGroup.add(tmp)

            self.lives -= 1
            if self.lives > 0:
                self.health = 100
            self.kill()

        self.image = self.base_image
        self.move(keys)
        self.rectifyPos()

class Level():
    def __init__(self, level):
        sporeDict = {
            "Spore_1": Spore_1,
            "Spore_2": Spore_2,
            "Spore_3": Spore_3,
            "Spore_4": Spore_4,
            "Premature_1": Premature_1,
            "Premature_2": Premature_2
        }

        data = gameData["levels"].get(level)

        self.strip = pygame.image.load(data["bg_strip"])
        self.wh_ratio = self.strip.get_height()/self.strip.get_width()
        self.bgm = data["bgm"]
        self.name = level

        self.image = pygame.transform.scale(self.strip, (screen.get_width(), math.floor(screen.get_height()*self.wh_ratio)))
        self.rect = self.image.get_rect()
        self.resetMountPoint()


        self.speed = data["Level Speed"]
        self.min_speed = self.speed
        self.cloudDensity = data["cloudDensity"]
        self.cloudType = data["cloudType"]
        self.icon = pygame.image.load(data["icon"])
        self.icon_rect = self.icon.get_rect()

        self.briefing = data["briefing"]
        self.bossName = data["boss"]
        self.boss = sporeDict[self.bossName]
        self.bossBGM = data["boss_bgm"]

        self.wave = []
        self.pause = False

        self.boss_speed = data["boss_speed"] if "boss_speed" in data else 20
        self.boss_health = 500 if not "boss_health" in data else data["boss_health"]
        self.boss_legs = data["boss_legs"] if "boss_legs" in data else 3
        self.boss_lazer1 = data["boss_lazer1"] if "boss_lazer1" in data else "standard"
        self.boss_lazer2 = data["boss_lazer2"] if "boss_lazer2" in data else "bomb"

        for spore in data["wave"]:
            if isinstance(spore, list):
                sp_list = [sporeDict[sp] for sp in spore]
                self.wave.append(sp_list)
            else:
                self.wave.append(sporeDict[spore])

        self.waveTime = 20*FPS
        self.waveIndex = 0
    def resetMountPoint(self):
        self.rect.midbottom = screen.get_rect().midbottom

    def scroll(self):
        if self.rect.topleft[1] > 0:
            self.resetMountPoint()
        self.rect.y += self.speed

    def update(self, alphaVal=150):
        self.scroll()
        self.image.set_alpha(alphaVal)

class backgroundObject(pygame.sprite.Sprite):
    def __init__(self, image=None, template="island", speedVector=pygame.math.Vector2(0, 0), pos=(0, 0)):
        super().__init__()
        if isinstance(image, str):
            self.image = pygame.image.load(image)
        else:
            objects = os.listdir(f"levels/bgObjects/{template}")
            random.shuffle(objects)
            self.image = pygame.image.load(f"levels/bgObjects/{template}/{objects[0]}")
        self.rect = self.image.get_rect()
        self.vec = speedVector
        self.rect.center = pos
    def update(self):
        self.rect.center += self.vec
        if self.rect.midtop[1] > screen.get_height():
            self.kill()


class Text(pygame.sprite.Sprite):
    def __init__(self, msg, script, textColor, pos=(0, 0), shadow=False):
        super().__init__()

        img = script.render(msg, None, textColor)
        if not shadow:
            self.image = img.copy()
        else:
            self.image = pygame.Surface((img.get_width()*1.02, img.get_height()*1.02)).convert_alpha()
            self.image.fill((23, 16, 1))
            self.image.set_colorkey((23, 16, 1))
            shadowText = Text(msg, script, BLACK)
            shadowText.rect.topleft = (3, 2)

            self.image.blit(shadowText.image, shadowText.rect)
            self.image.blit(img, (0, 0))

        self.rect = self.image.get_rect()
        self.color = textColor
        self.rect.center = pos
        self.alphaValue = 255
        self.deltaA = -20
    def blink(self):
        self.alphaValue += self.deltaA
        if not isInBounds(self.alphaValue, 255, 0):
            self.deltaA *= -1
        self.image.set_alpha(self.alphaValue)

class Lazer(pygame.sprite.Sprite):
    def __init__(self, l_type="standard", damage=10, mount_point=(0,0), speed=10, angle=90, sizeFactor=1):
        super().__init__()
        laser = pygame.image.load(f"lazers/{l_type}.png")
        self.copy = pygame.transform.scale_by(laser, sizeFactor)
        self.image = pygame.transform.rotate(self.copy, angle)

        self.corrVec = pygame.math.Vector2(self.copy.get_width()//2, 0).rotate(angle)

        self.sizeFactor = sizeFactor
        self.rect = self.image.get_rect()
        self.rect.center = mount_point + self.corrVec
        self.speed = speed
        #x_vec = speed * cos(radians(angle))
        #y_vec = -speed * sin(radians(angle))
        self.vel = pygame.math.Vector2(self.speed, 0).rotate(-angle)
        self.sender = None
        self.oppGroup = None
        self.damage = damage

    def update(self):
        self.rect.center += self.vel

        if not isInBounds(self.rect.x, screen.get_width(), 0) or not isInBounds(self.rect.y, screen.get_height(), 0):
            self.kill()

        if pygame.sprite.spritecollideany(self, self.oppGroup):
            sprite = pygame.sprite.spritecollideany(self, self.oppGroup)
            if hasattr(sprite, "health"):
                if hasattr(sprite, "premature"):
                    if not sprite.invincible:
                        sprite.premature.health -= self.damage
                sprite.health -= self.damage
                if sprite.health <= 0:
                    if hasattr(self.sender, "points"):
                        self.sender.points += sprite.points
            exp = Explosion(explosion, self.sizeFactor, 3, self.rect.center)
            fireGroup.add(exp)
            self.kill()


class dummySprite(pygame.sprite.Sprite):
    def __init__(self, color=GREEN):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.rect = self.image.get_rect()
        self.x_speed = 5
        self.y_speed = 5
        self.image.fill(color)
    def update(self):
        if not isInBounds(self.rect.y, screen.get_height(), 0, self.image.get_height()//2):
            self.y_speed *= -1
        if not isInBounds(self.rect.x, screen.get_width(), 0, self.image.get_width()//2):
            self.x_speed *= -1

        self.rect.x += self.x_speed
        self.rect.y += self.y_speed

class Gun(pygame.sprite.Sprite):
    def __init__(self, target, mountPoint=(0, 0), sizeFactor=1, staticAngle=90, type="standard"):
        super().__init__()
        self.mountpoint = mountPoint
        self.target = target
        self.sizeFactor = sizeFactor
        self.lazType = type
        self.damage = 5


        buffImage = pygame.image.load("turrets/gun.png")
        baseImage = pygame.image.load("turrets/turret_frame.png")

        self.image = pygame.transform.scale_by(buffImage, sizeFactor)
        self.turret_frame = pygame.transform.scale_by(baseImage, sizeFactor)

        self.image_cp = self.image.copy()
        self.rect = self.image.get_rect()
        self.frame_rect = self.turret_frame.get_rect()
        self.frame_rect.center = self.mountpoint

        self.x_dist = 0
        self.y_dist = 0
        self.angle = staticAngle
        self.correctionVector = None
        self.angleCheck = 0

        self.sender = None
        self.oppGroup = None

        self.lazerSpeed = 10

        self.maxCool = 10
        self.cooldown = self.maxCool
        if self.target is None:
            self.rotate()

    def get_angle(self):
        self.x_dist = self.rect.centerx - self.target.rect.centerx
        self.y_dist = self.rect.centery - self.target.rect.centery

        if self.x_dist > 0:
            self.angleCheck = 180
        else:
            self.angleCheck = 0
        if not isInBounds(self.x_dist, 1, -1) and not isInBounds(self.y_dist, 1, -1):
            self.angle = -math.degrees(math.atan(self.y_dist/self.x_dist)) + self.angleCheck

    def fire(self, offset=pygame.math.Vector2(0, 0), sizeFactor=0.3):
        exp = Explosion(explosion, sizeFactor, 2)

        tmp = Lazer(self.lazType, self.damage, speed=self.lazerSpeed, angle=self.angle, sizeFactor=sizeFactor)
        tmp.rect.center = self.rect.center + offset
        exp.rect.center = self.rect.center + self.correctionVector + offset

        tmp.sender = self.sender
        tmp.oppGroup = self.oppGroup

        fireGroup.add(exp)
        fireGroup.add(tmp)

    def rotate(self):
        self.image = pygame.transform.rotate(self.image_cp, self.angle)
        self.rect = self.image.get_rect()
        self.correctionVector = pygame.math.Vector2(self.image_cp.get_width()//3, 0).rotate(-self.angle)

        self.rect.center = self.mountpoint + self.correctionVector

    def update(self, fireOffset=pygame.math.Vector2(0, 0), sizeFactor=1):
        self.frame_rect.center = self.mountpoint

        if self.target is not None:
            self.get_angle()
            self.rotate()

        if self.cooldown <= 0:
            self.fire(fireOffset, sizeFactor)
            self.cooldown = self.maxCool
        else:
            self.cooldown -= 1


class HealthBar(pygame.sprite.Sprite):
    def __init__(self, sprite, stdLength=screen.get_width()//3, window=screen):
        super().__init__()
        self.sprite = sprite

        self.standard_length = stdLength
        self.image = pygame.Surface((self.standard_length, window.get_height()//20))
        self.image.fill(GREEN)

        self.copy = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.bottomleft = window.get_rect().bottomleft

    def update(self):
        if self.sprite.health > 0:
            health_pct = (self.sprite.health/self.sprite.maxHealth)
        else:
            health_pct = 0
        self.image = pygame.transform.scale(self.copy, (health_pct * self.standard_length, self.copy.get_height()))
        if isInBounds(self.sprite.health, 100, 65):
            self.image.fill(GREEN)
        elif isInBounds(self.sprite.health, 65, 45):
            self.image.fill(YELLOW)
        elif isInBounds(self.sprite.health, 45, 0):
            self.image.fill(RED)

        self.rect = self.image.get_rect()
        self.rect.bottomleft = screen.get_rect().bottomleft

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, power, speed=1):
        super().__init__()
        self.image = pygame.image.load(f"PowerUps/{power}.png")
        self.rect = self.image.get_rect()

        self.speed = speed
        self.rect.midbottom = (random.randint(screen.get_width()//10, screen.get_width() * 9//10), 0)
    def update(self):
        if self.rect.midtop[1] < screen.get_height():
            self.rect.y += self.speed
        else:
            self.kill()
        if pygame.sprite.spritecollideany(self, playerGroup):
            pygame.mixer.Sound("SFX/powerUp_collect.wav").play()
class Bomb(PowerUp):
    def __init__(self):
        super().__init__("bomb")
    def update(self):
        if pygame.sprite.spritecollideany(self, playerGroup):
            sprite = pygame.sprite.spritecollideany(self, playerGroup)
            if isinstance(sprite, Player):
                sprite.bombs += 1
                self.kill()
        super().update()
class Heal(PowerUp):
    def __init__(self):
        super().__init__("heal")
    def update(self):
        if pygame.sprite.spritecollideany(self, playerGroup):
            sprite = pygame.sprite.spritecollideany(self, playerGroup)
            if isinstance(sprite, Player):
                sprite.health = 100
                self.kill()
        super().update()
class OneUp(PowerUp):
    def __init__(self):
        super().__init__("1up")
    def update(self):
        if pygame.sprite.spritecollideany(self, playerGroup):
            sprite = pygame.sprite.spritecollideany(self, playerGroup)
            if isinstance(sprite, Player):
                sprite.health = 100
                sprite.lives += 1
                self.kill()
        super().update()
class Wingman(Player):
    def __init__(self, player):
        super().__init__(player.name)
        self.base_image = pygame.transform.scale_by(player.base_image, 0.75)
        self.left_img = pygame.transform.scale_by(player.left_img, 0.75)
        self.right_img = pygame.transform.scale_by(player.right_img, 0.75)

        self.image = self.base_image
        self.rect = self.image.get_rect()

        self.player = player
        self.health = 50
        self.bombs = 0
        self.lives = 1
        self.side = "Left"
    def update(self):
        super().update()
        if self.side == "Left":
            self.rect.midright = self.player.rect.bottomleft
        elif self.side == "Right":
            self.rect.midleft = self.player.rect.bottomright
        if self.player.health <= 0:
            self.kill()
    pass
class WingUp(PowerUp):
    def __init__(self, player):
        super().__init__("bomb")
        self.image = pygame.transform.scale_by(player.image, 0.5)
        self.rect = self.image.get_rect()
    def update(self):
        if pygame.sprite.spritecollideany(self, playerGroup):
            sprite = pygame.sprite.spritecollideany(self, playerGroup)
            if isinstance(sprite, Player):
                wing1 = Wingman(sprite)
                wing2 = Wingman(sprite)

                wing1.side = "Left"
                wing2.side = "Right"

                wingmanGroup.add(wing1)
                wingmanGroup.add(wing2)
                self.kill()
        super().update()

class Prema_Part(pygame.sprite.Sprite):
    def __init__(self, prema_type, bodypart, target, parent, resizeFactor=1, points=500):
        super().__init__()
        buffer = pygame.image.load(f"bosses/{prema_type}/{prema_type}-{bodypart}.png")
        self.image = pygame.transform.scale_by(buffer, resizeFactor)
        self.rect = self.image.get_rect()

        self.invincible = False
        self.points = points

        self.bodypart = bodypart
        self.premature = parent
        self.health = 300
        self.maxHealth = 300
        self.oppGroup = playerGroup
        self.target = target
        self.mountpoint = (0, 0)
        self.loot = powerUpTypes
        self.parent = parent
        self.gun = None
        self.bulletSize = 0

    def genGun(self, gunType, size, maxCool=75, damage=25, bulletSize=0.5):
        self.gun = Gun(self.target, self.rect.center, size, type=gunType)
        self.gun.sender = self.parent
        self.gun.oppGroup = self.oppGroup
        self.gun.lazerSpeed = 5
        self.gun.damage = damage
        self.gun.maxCool = maxCool
        self.bulletSize = bulletSize

        self.gun.frame_rect.midtop = self.gun.mountpoint

    def update(self, gunActive=False):
        if self.health <= 0:
            if len(wingmanGroup.sprites()) > 1:
                if WingUp in self.loot:
                    self.loot.remove(WingUp)

            pType = self.loot[random.randint(0, len(self.loot) - 1)]
            pUp = pType() if pType != WingUp else pType(playerGroup.sprites()[-1])
            if not pygame.sprite.spritecollideany(pUp, powerUpGroup):
                pUp.rect.center = self.rect.center
                powerUpGroup.add(pUp)

            tmp = Explosion(explosion, 3, pos=self.rect.center, sound="SFX/ship-explosion.wav")
            sporeGroup.add(tmp)
            self.kill()
        elif isinstance(self.gun, Gun):
            self.gun.mountpoint = self.rect.center
            self.gun.frame_rect.center = self.gun.rect.center
            self.gun.update(sizeFactor=self.bulletSize)

            if gunActive:
                for player in playerGroup.sprites():
                    if dist(player.rect.center, self.gun.rect.center) < 250:
                        self.gun.fire()

    def draw(self, window):
        window.blit(self.image, self.rect)

    def draw_premagun(self, window):
        window.blit(self.gun.turret_frame, self.gun.frame_rect)
        window.blit(self.gun.image, self.gun.rect)

class Premature_1():
    def __init__(self, target, resizeFactor=1, oppGroup=playerGroup, health=500, legs=3, lazertype="standard"):
        self.type = "Premature_1"
        self.body = Prema_Part(self.type, "body", target, self, resizeFactor, 300)

        self.weakspot_map = pygame.image.load(f"bosses/{self.type}/{self.type}-weakspotmap.png")
        self.map_rect = self.weakspot_map.get_rect()

        self.target = target

        self.main_gun = Gun(target, (self.body.rect.centerx, self.body.image.get_height()//3), resizeFactor+3)
        self.main_gun.lazType = lazertype
        self.main_gun.sender = self
        self.main_gun.oppGroup = oppGroup
        self.main_gun.lazerSpeed = 5
        self.main_gun.damage = 25
        self.main_gun.maxCool = 75

        self.main_gun.frame_rect.midtop = self.main_gun.mountpoint

        self.body.image.blit(self.main_gun.turret_frame, self.main_gun.frame_rect)
        self.body.rect.midbottom = screen.get_rect().midtop
        self.body.invincible = True
        self.body.health = health

        self.body.health = health
        self.maxHealth = self.body.health

        self.maxCool = 100
        self.coolDown = 5

        self.lig_left = []
        self.lig_right = []
        self.ligaments = 0

        for i in range(legs):
            left = Prema_Part(self.type, "ligament-left", target, self, resizeFactor, 150)
            right = Prema_Part(self.type, "ligament-right", target, self, resizeFactor, 150)

            if i >= 3:
                left.rect = Rect(0, 0, left.rect.width, left.rect.height // 10)
                right.rect = Rect(0, 0, right.rect.width, right.rect.height // 10)

            self.lig_left.append(left)
            self.lig_right.append(right)

            left.health += self.maxHealth * 0.125
            right.health += self.maxHealth * 0.125

            self.maxHealth += left.health + right.health

            self.ligaments += 2

        self.health = self.maxHealth
    def fire(self, type, angle, speed=2):
        tmp = Lazer(type, 15, self.body.rect.center + pygame.math.Vector2(0, self.body.image.get_height()//5), speed, angle, 0.75)
        tmp.sender = self
        tmp.oppGroup = playerGroup

        fireGroup.add(tmp)

    def spawn_spore(self, spore):
        tmp = spore(self.target)
        if tmp.rect.midbottom[1] < screen.get_height()//2:
            sporeGroup.add(tmp)

    def place_ligaments(self):
        for i, left in enumerate(self.lig_left):
            left.rect.topright = (
            0 + self.body.rect.x, self.body.image.get_height() * (i) // (len(self.lig_left) + 2) + self.body.rect.y)

            if left.health <= 0:
                self.health -= 25
                self.lig_left.remove(left)
                self.ligaments -= 1

        for i, right in enumerate(self.lig_right):
            right.rect.topleft = (self.body.rect.x + self.body.image.get_width(),
                                  self.body.rect.y + self.body.image.get_height() * (i) // (len(self.lig_right) + 2))
            if right.health <= 0:
                self.health -= 25
                self.lig_right.remove(right)
                self.ligaments -= 1

    def update(self, type="bomb"):
        print(self.body.health, self.health)

        if self.ligaments <= 0:
            self.body.invincible = False
        elif dist(self.body.rect.midtop, screen.get_rect().midtop) > 1:
            self.body.rect.centery += 2

        if self.body.health > 0:
            if self.main_gun:
                self.main_gun.mountpoint = self.body.rect.center
                self.main_gun.update()

            self.place_ligaments()

            if self.coolDown <= 0:
                if not self.body.invincible:
                    self.spawn_spore(Spore_2)
                if isInBounds(self.health/self.maxHealth, 0.75, 0.25):
                    for i in range(5):
                        self.fire(type, 45+i*64, 5)
                if self.health/self.maxHealth < 0.25:
                    for i in range(10):
                        self.fire("bomb", 45+i*32, 1)
                if self.health/self.maxHealth < 0.15:
                    self.spawn_spore(Spore_4)

                self.coolDown = self.maxCool
            else:
                self.coolDown -= 1

        self.body.health = self.health

    def draw(self, window):
        if self.body.health > 0:
            window.blit(self.body.image, self.body.rect)
            window.blit(self.main_gun.turret_frame, self.main_gun.frame_rect)


        for item in self.lig_right + self.lig_left:
            if item.health > 0:
                item.draw(window)

    def draw_gun(self, window):
        window.blit(self.main_gun.image, self.main_gun.rect)

class Premature_2(Premature_1):
    counter = 0
    units = 0
    def __init__(self, target, *args, **kwargs):

        pygame.mixer.music.load(f"BGM/miniboss.ogg")
        pygame.mixer.music.play(-1)

        self.units += 1
        self.resizeFactor = 3
        self.type = "Premature_2"
        self.body = Prema_Part(self.type, "body", target, self, self.resizeFactor, 800)

        self.weakspot_map = pygame.image.load(f"bosses/{self.type}/{self.type}-weakspotmap.png")
        self.map_rect = self.weakspot_map.get_rect()

        self.target = target

        self.body.rect.midbottom = (screen.get_width()//2, -screen.get_height())
        self.body.invincible = True
        self.body.health = kwargs["health"] if "health" in kwargs else 500
        self.maxHealth = self.body.health

        self.maxCool = 125
        self.coolDown = 5
        self.ligaments = 0

        #self.body.genGun("amp", 3, self.maxCool)
        #self.body.gun.cooldown = self.maxCool
        self.main_gun = None

        if "level" in kwargs:
            self.level = kwargs["level"]
            self.level.pause = True
        else:
            self.level = None

        self.lig_left = [Prema_Part(self.type, "center", target, self, self.resizeFactor, points=500)]
        self.lig_right = [Prema_Part(self.type, "center", target, self, self.resizeFactor, points=500)]

        self.lig_left.append(Prema_Part(self.type, "left-corner", target, self, self.resizeFactor, points=500))
        self.lig_left.append(Prema_Part(self.type, "center-mid", target, self, self.resizeFactor, points=500))
        self.lig_left.append(Prema_Part(self.type, "up", target, self, self.resizeFactor, points=500))

        self.lig_right.append(Prema_Part(self.type, "right-corner", target, self, self.resizeFactor, points=500))
        self.lig_right.append(Prema_Part(self.type, "center-mid", target, self, self.resizeFactor, points=500))
        self.lig_right.append(Prema_Part(self.type, "up", target, self, self.resizeFactor, points=500))

        for i in self.lig_left + self.lig_right:
            i.genGun("amp", 3, maxCool=50)
            i.gun.maxCool = self.maxCool
            i.gun.cooldown = self.coolDown

            i.health += self.body.health * 0.125

            self.maxHealth += i.health
            self.ligaments += 1

        self.health = self.maxHealth

    def place_ligaments(self):
        for i, lig in enumerate(self.lig_left):
            if i < 2:
                if i > 0:
                    lig.rect.midright = self.lig_left[i - 1].rect.midleft
                else:
                    lig.rect.midright = self.body.rect.midleft
            else:
                lig.rect.midtop = self.lig_left[i - 1].rect.midbottom

            if lig.health <= 0:
                self.lig_left.remove(lig)
                self.ligaments -= 1

        for i, lig in enumerate(self.lig_right):
            if i < 2:
                if i > 0:
                    lig.rect.midleft = self.lig_right[i - 1].rect.midright
                else:
                    lig.rect.midleft = self.body.rect.midright
            else:
                lig.rect.midtop = self.lig_right[i - 1].rect.midbottom

            if lig.health <= 0:
                self.lig_right.remove(lig)
                self.ligaments -= 1

    def update(self, type="standard"):
        self.counter += 1

        if self.health <= 0:
            if self.level:
                self.level.pause = False
                #self.level.waveIndex += 1

                pygame.mixer.music.load(self.level.bgm)
                pygame.mixer.music.play(-1)


        super().update(type)

        if self.ligaments <= 0:
            self.maxCool = 25
            self.body.rect.centerx += 12*math.sin(0.12*self.counter)
            self.body.rect.centery -= 12*math.cos(0.12*self.counter)

            if self.coolDown <= 0:
                for i in range(5):
                    self.fire("bomb", 45 + i * 64, 5)
                    self.fire("plasma", 30 + i * 64, 5)
                    self.coolDown = self.maxCool

            if dist(self.body.rect.center, screen.get_rect().center) > 5:
                self.body.rect.centery += 1 if self.body.rect.centery < screen.get_rect().centery else -1


    def draw_gun(self, window):
        if isinstance(self.body.gun, Gun):
            self.body.draw_premagun(window)
        for lig in self.lig_left + self.lig_right:
            if lig.health > 0:
                lig.draw_premagun(window)


class Spore_Generic(pygame.sprite.Sprite):
    def __init__(self, target, tagNumber, weaponType, sizeFactor=1, points=50):
        super().__init__()
        buffImg = pygame.image.load(f"enemies/Spore-{tagNumber}.png")
        self.image = pygame.transform.scale_by(buffImg, sizeFactor)
        self.rect = self.image.get_rect()
        self.target = target
        self.sizeFactor = sizeFactor
        self.oppGroup = playerGroup
        self.points = points


        self.health = 50
        self.weaponType = weaponType
        self.speed = 5
        self.direction = 1
    def update(self):
        if not isInBounds(self.rect.centery, self.image.get_height() + screen.get_height(), -screen.get_height()//2, self.image.get_height()//2):
            self.kill()
        if self.health <= 0:
            tmp = Explosion(explosion, 3, pos=self.rect.center, sound="SFX/ship-explosion.wav")
            sporeGroup.add(tmp)
            self.kill()
class Spore_1(Spore_Generic):
    def __init__(self, target):
        super().__init__(target, 1, "bomb", points=15)
        self.rect.midbottom = (random.randint(self.image.get_width(), screen.get_width() - self.image.get_width()), 0)

        self.health = 25
        self.maxCool = 50
        self.cooldown = 5
    def fire(self):
        tmp = Lazer(self.weaponType, 10, self.rect.midbottom, random.randint(-3, 3), random.randint(-90, 90), 0.4)
        tmp.sender = self
        tmp.oppGroup = self.oppGroup

        fireGroup.add(tmp)
        allSprites.add(tmp)
    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        else:
            self.fire()
            self.cooldown = self.maxCool
        self.rect.centery += self.speed
        super().update()
class Spore_2(Spore_Generic):
    def __init__(self, target):
        super().__init__(target, 2, "standard", points=25)
        self.rect.midbottom = [random.randint(0, screen.get_width()), -random.randint(0, screen.get_height()//3)]


        self.health = 25
        self.speed = 3
        self.maxCool = 50
        self.cooldown = self.maxCool
    def fire(self):
        tmp = Lazer(self.weaponType, 5, self.rect.center, 6, -90, 0.2)
        tmp.sender = self
        tmp.oppGroup = self.oppGroup

        fireGroup.add(tmp)
        allSprites.add(tmp)
    def update(self):
        self.rect.y += self.speed
        if self.rect.midtop[1] > screen.get_height():
            self.kill()
        self.cooldown -= 1
        if self.cooldown <= 0:
            self.cooldown = self.maxCool
            self.fire()

        super().update()

class Spore_3(Spore_Generic):
    def __init__(self, target):
        super().__init__(target, 3, "bomb")
        self.x_dist = 0
        self.y_dist = 0
        self.angle = 0
        self.angleCheck = 0
        self.coolDown = 0
        self.maxCool = 100
        self.speed = 1

        self.random_val = (random.randint(1, 10))/50
        self.spawnPrep()
    def spawnPrep(self):
        self.direction = -1
        self.rect.midtop = screen.get_rect().midbottom
        self.rect.x = random.randint(screen.get_width()//6, screen.get_width() * 5//6)

    def get_dist(self):
        self.x_dist = self.target.rect.centerx - self.rect.centerx
        self.y_dist = self.target.rect.centery - self.rect.centery
    def get_angle(self):
        if self.x_dist < 0:
            self.angleCheck = 180
        else:
            self.angleCheck = 0

        if not isInBounds(self.x_dist, 1, -1) and not isInBounds(self.y_dist, 1, -1):
            self.angle = -math.degrees(math.atan(self.y_dist/self.x_dist)) + self.angleCheck
    def fire(self):
        tmp = Lazer(self.weaponType, 20, self.rect.midbottom, 2, self.angle, 0.5)
        tmp.sender = self
        tmp.oppGroup = playerGroup

        fireGroup.add(tmp)
        allSprites.add(tmp)
    def update(self):
        if self.rect.midbottom[1] < 0:
            self.kill()

        self.get_dist()
        self.get_angle()
        if self.coolDown < 0 and self.y_dist > 0:
            self.fire()
            self.coolDown = self.maxCool
        else:
            self.coolDown -= 1
        self.rect.centerx += 5*math.sin(self.rect.centery * self.random_val)

        self.rect.centery += self.speed*self.direction
        super().update()
class Spore_4(Spore_Generic):
    def __init__(self, target, speed=5):
        super().__init__(target, 4, "standard", 2)
        self.direction = 1
        self.gunAngle = 0
        self.speed = speed
        self.turrets = []
        self.spawnPrep()

        for turret in self.turrets:
            turret.oppGroup = self.oppGroup
            turret.sender = self

            turret.maxCool = random.randint(30, 60)

            self.image.blit(turret.turret_frame, turret.frame_rect)
            self.image.blit(turret.image, turret.rect)
    def spawnPrep(self):
        tmpList = [1, -1]
        random.shuffle(tmpList)

        y = random.randint(0, screen.get_height())

        self.direction = tmpList[0]
        self.gunAngle = 90 if y > self.target.rect.y else -90
        self.generateBarracks()

        if self.direction < 0:
            self.rect.midleft = (screen.get_width(), y)
        elif self.direction > 0:
            self.rect.midright = (0, y)

        if self.direction < 0:
            self.image = pygame.transform.rotate(self.image, 180)

    def fire(self):
        for gun in self.turrets:
            gun.update(fireOffset=pygame.math.Vector2(self.rect.topleft[0], self.rect.topleft[1]), sizeFactor=0.25)

    def update(self):
        self.fire()
        self.rect.x += self.speed * self.direction
        if self.direction > 0:
            if self.rect.midleft[0] > screen.get_width():
                self.kill()
        elif self.direction < 0:
            if self.rect.midright[0] < 0:
                self.kill()
        super().update()

    def generateBarracks(self, num=10):
        bigBound = num-1 if self.direction > 0 else num
        smallBound = 0 if self.direction > 0 else 1
        for i in range(num):
            if isInBounds(i, bigBound, smallBound):
                tmp = Gun(None, ((i * self.image.get_width()/(num)), self.rect.centery), 1, staticAngle=self.gunAngle)
                self.turrets.append(tmp)
class Explosion(pygame.sprite.Sprite):
    def __init__(self, seq, size=1, speed=1, pos=(0, 0), loop=False, sound=None):
        super().__init__()
        self.seq = []
        for img in seq:
            tmp = pygame.transform.scale_by(img, size).convert_alpha()
            tmp.set_colorkey(WHITE)
            self.seq.append(tmp)

        if isinstance(sound, str):
            self.sound = pygame.mixer.Sound(sound)
            explosionChannel.play(self.sound)


        self.image = self.seq[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.anim_index = 0
        self.speed = speed
        self.loop = loop
    def update(self):
        self.anim_index += self.speed
        if self.anim_index >= len(self.seq) - 1:
            if self.loop:
                self.anim_index = 0
            else:
                self.kill()
        else:
            self.image = self.seq[int(self.anim_index)]
class Video():
    def __init__(self, video):
        self.video=video
        self.maxFrames = len(self.video)
        self.index = 0
        self.alphaVal=255
    def play(self, speed=1):
        self.index += speed
        if self.index >= self.maxFrames - 1:
            self.index = 0
        screen.blit(self.video[int(self.index)], (0, 0))
        self.video[int(self.index)].set_alpha(self.alphaVal)
    def setAlpha(self, alphaVal):
        self.alphaVal=alphaVal
    def fadeIn(self, inc):
        if self.alphaVal <= 255:
            self.alphaVal += inc
    def fadeOut(self, inc):
        if self.alphaVal > 0:
            self.alphaVal -= inc
class SpecsCard(pygame.sprite.Sprite):
    def __init__(self, playerObj):
        super().__init__()

        self.image = pygame.Surface((screen.get_width() * 2//3, screen.get_height() * 1//2 + 50))
        self.image.fill((31, 0, 31))
        self.image.set_colorkey((31, 0, 31))
        self.rect = self.image.get_rect()

        self.titleFont = pygame.font.Font("fonts/SolomonsKey.ttf", 50)
        self.statFont = pygame.font.Font("fonts/SolomonsKey.ttf", 16)
        self.statColor = (128, 207, 72)

        self.playerObj = playerObj
        self.shipImg = pygame.transform.scale(self.playerObj.image.copy(), (self.image.get_width()//2 - 20, self.image.get_height() * 3//4))
        self.shipRect = self.shipImg.get_rect()
        self.shipRect.bottomleft = (10, self.image.get_height() - 25)

        self.title = Text(self.playerObj.name, self.titleFont, BLUE)
        self.weaponType = Text(f"Weapon: {self.playerObj.weaponType}", self.statFont, self.statColor)
        self.damageAmnt = Text(f"Weapon Damage: {self.playerObj.damage}", self.statFont, self.statColor)
        self.bombDamage = Text(f"Bomb Damage: {self.playerObj.bombDamage}", self.statFont, self.statColor)
        self.speedNum = Text(f"Movement Speed: {self.playerObj.speed}", self.statFont, self.statColor)

        text = [self.weaponType, self.damageAmnt, self.bombDamage, self.speedNum]

        self.title.rect.topleft = (10, 20)
        self.image.blit(self.shipImg, self.shipRect)
        self.image.blit(self.title.image, self.title.rect)

        i = 2
        for line in text:
            line.rect.topleft = (self.image.get_width()//2, self.image.get_height() * (i)//(len(text)+4))
            self.image.blit(line.image, line.rect)
            i += 1

def dist(pos1, pos2):
    a = pygame.math.Vector2(pos1)
    b = pygame.math.Vector2(pos2)

    return (a-b).length()

def isInBounds(x, big, small, offset=0):
    return ((x + offset) < big) and ((x - offset) > small)
def drawScanlines(thickness, alpha, window):
    for i in range(window.get_height()):
        if i % (thickness * 4) == 0:
            tmp = pygame.Surface((window.get_width(), thickness))
            tmp.fill((0, 0, 0))
            tmp.set_alpha(alpha)

            window.blit(tmp, (0, i))

def meanValue(list):
    return sum(list)/len(list)

def readVideo(file, window=None, threshold=-1, colorKey=WHITE, MaxFrames=-1, frameSkip=-1):
    video = cv2.VideoCapture(file)
    w, h = video.read()[1].shape[1::-1]
    resize = window.get_size() if isinstance(window, pygame.surface.Surface) else (w, h)
    seq = []

    frameCount = 0

    while True:
        ret, frame = video.read()
        if not ret:
            break

        if threshold > 0:
            copy = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            newImg = np.zeros_like(copy)
            newImg[copy > threshold] = copy[copy > threshold]
            frame = cv2.cvtColor(newImg, cv2.COLOR_GRAY2BGR)

        if frameCount >= frameSkip:
            tmp = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR").convert_alpha()
            tmp = pygame.transform.scale(tmp, resize)
            tmp.set_colorkey(colorKey)
            seq.append(tmp)
        frameCount += 1

        if MaxFrames > 0:
            if frameCount > MaxFrames:
                break
    return seq

# Load the explosion gif
explosion = readVideo("misc/explosion.gif")

# Load all the levels form the gameData.json file
levels = [Level(levelName) for levelName in gameData.get("levels")]

# Load sfx for clicking
clickEffect = pygame.mixer.Sound("SFX/cursor.wav")

# name of players
players = [
    "avalanche",
    "bullseye",
    "cobra"
]

# Which keys to use (see def showKeyMapping())
keymapping = [
    ["misc/key-1.png", "Fire bombs"],
    ["misc/key-2.png", "Arrow Keys to move"],
    ["misc/key-3.png", "Space to fire lazer"]
]

# define different types fo powerups
powerUpTypes = [Heal, OneUp, Bomb, WingUp]

# Testing the turret on the premature. Does the logic work??
def turretTest():
    dummy = dummySprite()
    prema_1 = Premature_1(dummy, 3, allSprites)

    allSprites.add(dummy)

    prema_1.body.rect.center = screen.get_rect().center
    dummy.rect.topleft = (screen.get_width() - 30, 30)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    for sprite in fireGroup:
                        sprite.kill()
                    startScreen()
                    exit()

        keys = pygame.key.get_pressed()
        if keys[K_DOWN]:
            prema_1.body.health -= 1
        if keys[K_UP]:
            prema_1.body.health += 1


        dummy.update()
        prema_1.update()
        fireGroup.update()
        sporeGroup.update()

        screen.fill(BLACK)
        prema_1.draw(screen)
        fireGroup.draw(screen)
        prema_1.draw_gun(screen)
        sporeGroup.draw(screen)
        screen.blit(dummy.image, dummy.rect)

        pygame.display.update()
        clock.tick(30)

# print a loading screen, mostly used when loading gifs.
def printLoadingScreen():
    font = pygame.font.Font("fonts/planet_joust_ownjx.otf", 50)
    title = Text("Loading....", font, GREEN, screen.get_rect().center)

    screen.fill(BLACK)
    screen.blit(title.image, title.rect)

    pygame.display.update()

# Show the keymappping
def showKeyMapping():
    # Loading fonts..
    font = pygame.font.Font("fonts/windows_command_prompt.ttf", 25)
    msgFont = pygame.font.Font("fonts/ChargeVector.ttf", 40)

    # Creating text images..
    msg = Text("Press Any key to continue", msgFont, WHITE)
    msg.rect.midtop = (screen.get_width()//2, screen.get_height() * 3//4)

    keyDisplay = []

    # set a timer for 3 seconds
    timer = 3*30

    # Position the images and text
    i = 0
    for item in keymapping:
        img = pygame.image.load(item[0])
        img.set_colorkey(BLACK)
        img.set_alpha(200)

        img_rect = img.get_rect()

        if i < 2:
            img_rect.midbottom = ((i+1) * screen.get_width()//3, screen.get_height()//3)
        else:
            img_rect.center = (screen.get_width()//2, screen.get_height()//2)

        dsc = Text(item[1], font, GREEN)
        dsc.rect.midtop = img_rect.midbottom

        keyDisplay.append(([img, img_rect], dsc))

        i += 1

    # display keymapping
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if timer <= 0:
                    return

        msg.blink()

        screen.fill(BLACK)
        if timer <= 0:
            screen.blit(msg.image, msg.rect)

        for key in keyDisplay:
            screen.blit(key[0][0], key[0][1])
            screen.blit(key[1].image, key[1].rect)

        timer -= 1
        pygame.display.update()
        clock.tick(30)

# Mission briefing...
def briefingRoom(player, advance=False):
    # Load music
    pygame.mixer.music.load("BGM/briefing-2.ogg")
    pygame.mixer.music.play(-1)

    icons = []
    names = []

    # Load ship image
    shipImg = pygame.transform.rotate(player.left_img, -90)
    shipRect = shipImg.get_rect()

    # Used to make bg dark
    shadeLayer = pygame.Surface(screen.get_size())
    shadeLayer.fill(BLACK)
    shadeLayer.set_alpha(100)

    # Load fonts
    levelFont = pygame.font.Font("fonts/ChargeVector.ttf", 25)
    letterFont = pygame.font.Font("fonts/windows_command_prompt.ttf", 25)
    titleFont = pygame.font.Font("fonts/windows_command_prompt.ttf", 70)
    MapFont = pygame.font.Font("fonts/planet_joust_ownjx.otf", 70)

    # Place icons
    for level in levels:
        # if the icon image is to big, then shrink it
        if sum(level.icon.get_size()) > 200:
            level.icon = pygame.transform.scale(level.icon, (100, 100))
            level.icon_rect = level.icon.get_rect()

        # organizing the icons placement depending on number of icons to be placed.
        level.icon_rect.centery = screen.get_height()//2
        level.icon_rect.centerx = (levels.index(level)+1) * screen.get_width()/(len(levels)+1)
        icons.append([level.icon, level.icon_rect])

        # Adding text to display names of the levels
        title = Text(level.name, levelFont, WHITE)
        title.image.set_alpha(150)
        title.rect.midtop = level.icon_rect.midbottom
        names.append(title)

    shipRect.center = icons[player.levelIndex][1].center
    # three seconds to countdown.
    count = 3*30

    title = Text("Map Room", MapFont, WHITE)
    title.rect.midtop = screen.get_rect().midtop
    # Print mission briefing now?? Y/N
    briefing = False

    # Done with mission briefing?
    briefingDone = False


    # if prev mission completed, advance.
    if advance:
        if not player.levelIndex >= len(levels) - 1:
            player.levelIndex += 1

    currentLevel = levels[player.levelIndex]

    # cursor for briefing..
    cursor = Text("#", letterFont, GREEN)
    cursor.image.fill(GREEN)
    cursor.image = pygame.transform.scale_by(cursor.image, 0.85)

    briefingTitle = Text("MISSION BRIEFING", titleFont, RED)
    briefingTitle.rect.midtop = screen.get_rect().midtop

    # prepare letters for briefing
    letters = []

    # parse briefing message in gameData.json
    i = 0
    color = GREEN
    for line in currentLevel.briefing:
        j = 0
        for char in line:
            if char == '\\':
                color = RED
                continue
            if char == "^":
                color = GREEN
                continue
            if char == '@':
                color = ORANGE
                continue
            tmp = Text(char, letterFont, color, ((j*12) + screen.get_width()//10, i*25+screen.get_height()//6))
            letters.append(tmp)
            j += 1
        i += 1
    letterIndex = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and briefingDone:
                    showKeyMapping()
                    main(levels[player.levelIndex], player)
                if event.key == pygame.K_ESCAPE and briefingDone:
                    startScreen()
                    exit()
                if not briefingDone:
                    letterIndex = len(letters) - 1
                    break

        # Color the screen black.
        screen.fill(BLACK)

        if not briefing:
            if title.rect.bottomleft[1] > 0:
                screen.blit(title.image, title.rect)
            if count <= 0:
                title.rect.y -= 10

        for icon in icons:
            name = names[icons.index(icon)]
            # if count > 10 seconds. Count initiates after advance. see (if advance: vvv)
            if count <= 0:
                # move everything upwards and prepare for mission briefing.
                icon[1].y -= 10
                name.rect.y -= 10

            # draw line between levels showing their connection. But only before briefing.
            if icons.index(icon) < len(icons) - 1 and not briefing:
                pygame.draw.line(screen, GREY, icon[1].center, icons[icons.index(icon)+1][1].center, 5)

            # show images and titles before briefing, not after.
            if not briefing:
                screen.blit(icon[0], icon[1])
                screen.blit(name.image, name.rect)

        # If the player has completed the previous level, move to next level (advance=True).
        if advance:
            if icons[player.levelIndex][1].centerx - shipRect.centerx > 0:
                shipRect.centerx += player.speed
            else:
                # when the player icon has moved to next level, stop animation and switch to briefing.
                advance = False
        else:
            # Ideally there should be a transition from map to briefing.
            # here we use the count variable as a sleep value before clearing for briefing.
            if count > 0:
                count -= 1

        # no matter what happens, the y coordinate of our little plane icon will stay the same as the center_y coordinate its corresponding icon.
        shipRect.centery = icons[player.levelIndex][1].centery

        # when the screen is clear, start briefing.
        if names[-1].rect.midbottom[1] < 0 and not briefing:
            briefing = True

        screen.blit(shadeLayer, (0, 0))
        if not briefing:
            screen.blit(shipImg, shipRect)

        if briefing:
            msgChannel.play(clickEffect)
            if letterIndex < len(letters) - 1:
                letterIndex += 1
            else:
                msgChannel.pause()
                briefingDone = True


            screen.blit(briefingTitle.image, briefingTitle.rect)

            for char in letters[:int(letterIndex)]:
                screen.blit(char.image, char.rect)


            cursor.image.fill(letters[int(letterIndex)].color)
            cursor.rect.midleft = letters[int(letterIndex)].rect.midright
            cursor.blink()

            screen.blit(cursor.image, cursor.rect)


        drawScanlines(1, 50, screen)

        pygame.display.update()
        clock.tick(45)


# Submenu. Menu for player selection
def playerSelect():
    printLoadingScreen()

    bg = Video(readVideo("video/player_select.mp4", screen))
    shadeLayer = pygame.Surface(screen.get_size())
    shadeLayer.fill(BLACK)
    shadeLayer.set_alpha(125)

    # Creating font for title and cursor
    titleFont = pygame.font.Font("fonts/planet_joust_ownjx.otf", 75)

    # Creating Player Objects for game
    cards = [SpecsCard(Player(name)) for name in players]
    cards[0].rect.midtop = screen.get_rect().midbottom

    # creating image using Text Class
    title = Text("Select Ship", titleFont, WHITE)

    # Positioning title screen for animation.
    title.rect.midbottom = screen.get_rect().midtop

    # Animation speed and acceleration with 1D vectoral quantities
    # title Animation
    cardSpd =-15
    titleSpd = 5

    cardAcc = calc_Accel(cards[0].rect.centery, screen.get_height()//2, cardSpd, 0)
    titleAcc = calc_Accel(title.rect.midtop[1], screen.get_rect().midtop[1], titleSpd, 0)

    # index to traverse ships by
    index = 0

    # checking if player has selected ship
    select = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                clickEffect.play()

                if event.key == pygame.K_LEFT:
                    index -= 1
                    break
                if event.key == pygame.K_RIGHT:
                    index += 1
                    break
                if event.key == pygame.K_ESCAPE:
                    startScreen()
                    exit()
                if event.key == pygame.K_RETURN:
                    select = True

        if index > len(cards) - 1:
            index = 0
        if index < 0:
            index = len(cards) - 1

        # Animating the title screen
        title.rect.y += titleSpd
        cards[0].rect.y += cardSpd

        # play background video
        bg.play(1)

        # Updating speed
        if not select:
            if titleSpd > 0:
                titleSpd += titleAcc
            if cardSpd < 0:
                cardSpd += cardAcc
        else:
            titleSpd += titleAcc
            cardSpd += cardAcc

            if cards[0].rect.y > screen.get_height():
                fadeScreen(screen, True)
                briefingRoom(cards[index].playerObj)
                startScreen()
                exit()

        screen.blit(shadeLayer, (0, 0))
        screen.blit(title.image, title.rect)
        screen.blit(cards[index].image, cards[0].rect)
        drawScanlines(1, 150, screen)

        pygame.display.update()
        clock.tick(30)

# The main menu
def startScreen():
    pygame.mixer.music.load("BGM/startscreen.ogg")
    pygame.mixer.music.play(-1)
    printLoadingScreen()

    favicon = pygame.image.load("levels/icons/earth-planet.png")
    favicon = pygame.transform.scale_by(favicon, screen.get_width()/favicon.get_width())
    f_rect = favicon.get_rect()
    f_rect.center = screen.get_rect().midright

    titleFont = pygame.font.Font("fonts/planet_joust_ownjx.otf", 75)
    subFont = pygame.font.Font("fonts/windows_command_prompt.ttf", 50)

    words = gameTitle.split(" ")
    for i in range(len(words)):
        title = Text(words[i], titleFont, WHITE)
        if i == 0:
            title.rect.topleft = (50, 50)
        else:
            title.rect.topleft = textGroup.sprites()[-1].rect.bottomleft
        textGroup.add(title)


    start = Text("Start", subFont, GREEN)
    menu = Text("Menu", subFont, GREEN)
    indev = Text("Indev", subFont, GREEN)
    quit = Text("Quit", subFont, GREEN)

    cursor = Text("#", subFont, GREEN)
    cursor.image.fill(GREEN)
    cursor.image = pygame.transform.scale_by(cursor.image, 0.85)
    textGroup.add(cursor)

    alphaVal = 50

    shadow = pygame.Surface(screen.get_size())
    shadow.fill(BLACK)
    shadow.set_alpha(alphaVal)

    menu_vid = readVideo("video/earth.mp4", screen, MaxFrames=50 * 15.05, frameSkip=10)
    planet_vid = Video(menu_vid)

    options = [start, indev, quit]
    opIndex = 0
    i = 0
    selectMode = False
    acc = 5
    speed = 0

    for option in options:
        option.rect.midleft = (50, screen.get_height()//2 + (option.image.get_height() * i + 5))
        i += 1
        textGroup.add(option)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYUP:
                clickEffect.stop()
            if event.type == pygame.KEYDOWN:
                clickEffect.play()
                if event.key == pygame.K_DOWN:
                    if opIndex < len(options) - 1:
                        opIndex += 1
                    else:
                        opIndex = 0
                    break
                if event.key == pygame.K_UP:
                    if opIndex > 0:
                        opIndex -= 1
                    else:
                        opIndex = len(options) - 1
                    break
                if event.key == pygame.K_RETURN:
                    if not selectMode:
                        selectMode = True
                    break

        if selectMode:
            i=0
            for sprite in textGroup.sprites():
                if sprite.rect.midtop[1] < screen.get_height():
                    sprite.rect.y += speed * (i+2)
                else:
                    sprite.kill()
                i += 1
            if speed < 20:
                speed += acc
            alphaVal += speed
            shadow.set_alpha(alphaVal)

            if (len(textGroup.sprites())) <= 0:
                if options[opIndex] == start:
                    playerSelect()
                    exit()
                elif options[opIndex] == quit:
                    pygame.quit()
                    exit()
                elif options[opIndex] == indev:
                    tmp = Player("avalanche")
                    tmp.levelIndex = 0

                    briefingRoom(tmp, True)
                    startScreen()
                    exit()
                else:
                    startScreen()
                    exit()


        cursor.rect.midright = options[opIndex].rect.midleft
        cursor.blink()

        planet_vid.play()
        screen.blit(shadow, (0, 0))

        textGroup.draw(screen)
        drawScanlines(1, 200, screen)

        pygame.display.update()
        clock.tick(30)

def fadeScreen(window, fadeOut=False):
    alpha = 0
    layer = pygame.Surface(window.get_size())

    while True:
        if alpha < 255:
            alpha += 3
            if fadeOut:
                pygame.mixer.music.set_volume(pygame.mixer.music.get_volume() - 0.01)
        if pygame.mixer.music.get_volume() <= 0:
            break

        layer.set_alpha(alpha)
        window.blit(layer, (0, 0))

        pygame.display.update()
        clock.tick(30)

    pygame.mixer.music.stop()
    pygame.mixer.music.unload()

    pygame.mixer.music.set_volume(1)


# Calculate 1D acceleration of an object given start/end distance and start/end speed
def calc_Accel(start_point, end_point, start_speed, end_speed):
    return (end_speed**2 - start_speed**2)/(2*(end_point - start_point))

def gameOver():
    headFont = pygame.font.Font("fonts/planet_joust_ownjx.otf", 75)
    subFont = pygame.font.Font("fonts/ChargeVector.ttf", 25)

    shadeLayer = pygame.Surface(screen.get_size())
    shadeLayer.fill(BLACK)
    shadeLayer.set_alpha(25)

    title = Text("Game Over", headFont, WHITE)
    subtitle = Text("Press anything to continue", subFont, WHITE)

    title.rect.midbottom = screen.get_rect().midtop
    subtitle.rect.topleft = screen.get_rect().midright

    titleSpeed = 15
    subtitleSpeed = -20

    titleAcc = calc_Accel(0, screen.get_height()//2, titleSpeed, 0)
    subAcc = calc_Accel(screen.get_width() + subtitle.image.get_width()//2, screen.get_width()//2, subtitleSpeed, 0)

    animated = False

    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    pygame.mixer.music.load("BGM/gameOver.ogg")
    pygame.mixer.music.play()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if animated:
                    startScreen()
                    exit()
                break

        screen.blit(shadeLayer, (0, 0))
        screen.blit(title.image, title.rect)
        screen.blit(subtitle.image, subtitle.rect)

        if title.rect.midbottom[1] < screen.get_height()//2:
            title.rect.y += titleSpeed
            titleSpeed += titleAcc
        if subtitle.rect.centerx > screen.get_width()//2:
            subtitle.rect.x += subtitleSpeed
            subtitleSpeed += subAcc
        else:
            animated = True

        pygame.display.update()
        clock.tick(30)

def creditsScreen(p1):

    bgVid = Video(readVideo("video/moon.mp4",screen))

    pygame.mixer.music.load("BGM/credits.ogg")
    pygame.mixer.music.play()

    p1.rect.midtop = screen.get_rect().midbottom

    header = pygame.font.Font("fonts/SolomonsKey.ttf", 50)
    scoreFont = pygame.font.Font("fonts/windows_command_prompt.ttf", 25)
    finalFont = pygame.font.Font("fonts/ChargeVector.ttf", 75)
    subFont = pygame.font.Font("fonts/SolomonsKey.ttf", 15)

    pointsTitle = Text("Player Score", header, BLUE)
    playerScore = Text(f"{p1.points}", scoreFont, GREEN)

    playerScore.rect.midbottom = screen.get_rect().midtop
    pointsTitle.rect.midbottom = playerScore.rect.midtop

    msg = Text("Thanks for playing!!", finalFont, WHITE)
    subtitle = Text("Good Job Soldier", subFont, WHITE)

    subtitle.rect.midbottom = screen.get_rect().midtop
    msg.rect.midbottom = subtitle.rect.midtop



    credits = gameData["credits"]
    letters = []
    letterIndex = 0

    mount = (15, screen.get_height()//3)

    i = 0
    for line in credits:
        j = 0
        for char in line:
            tmp = Text(char, scoreFont, GREEN, (mount[0] + j*13, mount[1] + i*20))
            letters.append(tmp)
            j += 1
        i += 1

    bg1 = pygame.Surface(screen.get_size())
    bg1.fill(BLACK)
    bg1.set_alpha(15)

    count = 0
    phase = 0

    # First loop that prints the ending text
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        for letter in letters[:letterIndex]:
            screen.blit(letter.image, letter.rect)

        if letterIndex < len(letters):
            letterIndex += 1
        else:
            count += 1

            if count > 3*30:
                break

        drawScanlines(1, 150, screen)
        pygame.display.update()
        clock.tick(30)

    # Part two of the ending. Show the players achievements and thank player.
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if phase > 1:
                    fadeScreen(screen, True)
                    startScreen()
                    exit()

        bgVid.play()

        if phase <= 0:
            pointsTitle.rect.midbottom = playerScore.rect.midtop

            if playerScore.rect.midtop[1] <= screen.get_height()//2:
                playerScore.rect.y += 3
                count = 0
            elif count > FPS:
                if pointsTitle.rect.midtop[1] <= screen.get_height():
                    playerScore.rect.y += 5
                else:
                    count = 0
                    phase += 1
        if phase == 1:
            if msg.rect.midbottom[1] < screen.get_height()//2:
                msg.rect.y += 3
            else:
                phase += 1

            subtitle.rect.midtop = msg.rect.midbottom

        screen.blit(msg.image, msg.rect)
        screen.blit(subtitle.image, subtitle.rect)

        screen.blit(pointsTitle.image, pointsTitle.rect)
        screen.blit(playerScore.image, playerScore.rect)

        drawScanlines(1, 15, screen)

        pygame.display.update()
        clock.tick(30)
        count += 1

# The main mechanics of the game.
def main(level, p1):
    for sprite in sporeGroup.sprites():
        sprite.kill()
    for sprite in allSprites.sprites():
        sprite.kill()
    for sprite in healthBarGroup.sprites():
        sprite.kill()
    for sprite in playerGroup.sprites():
        sprite.kill()
    for sprite in allClouds.sprites():
        sprite.kill()
    for sprite in wingmanGroup.sprites():
        sprite.kill()

    level.speed = level.min_speed
    level.waveIndex = 0
    level.rect.midbottom = screen.get_rect().midbottom

    p1.rect.center = screen.get_rect().center
    playerGroup.add(p1)
    allSprites.add(p1)

    prema = level.boss(p1, 3, health=level.boss_health, legs=level.boss_legs, lazertype=level.boss_lazer1)

    healthBar = HealthBar(p1)
    healthBarGroup.add(healthBar)

    bossBar = HealthBar(prema, screen.get_width()//2)

    font = pygame.font.Font("fonts/planet_joust_ownjx.otf", 50)
    subtitle = pygame.font.Font("fonts/ChargeVector.ttf", 25)
    pointFont = pygame.font.Font("fonts/windows_command_prompt.ttf", 25)

    subtitle.set_italic(True)

    warningFont = pygame.font.Font("fonts/ChargeVector.ttf", 75)

    winText = Text("LEVEL COMPLETE", font, WHITE)
    winText.rect.center = screen.get_rect().center

    warning = Text("WARNING !!", warningFont, RED)
    warning.rect.center = screen.get_rect().center
    warning.deltaA = -45

    sideMsg = Text("Press Enter to continue", subtitle, WHITE)
    sideMsg.rect.midtop = winText.rect.midbottom

    pointsTitle = Text("Points", pointFont, WHITE, shadow=True)
    pointsTitle.rect.midtop = screen.get_rect().midtop


    for i in range(level.cloudDensity):
        tmp = Cloud(level.cloudType)
        if not pygame.sprite.spritecollideany(tmp, allClouds):
            if i % 2 == 0:
                tmp.image.set_alpha(200)
                cloudsGroup2.add(tmp)
            else:
                cloudsGroup1.add(tmp)
            allClouds.add(tmp)

    shade_layer = pygame.Surface(screen.get_size())
    shade_layer.fill(BLACK)
    shade_layer.set_alpha(150)

    pygame.mixer.music.load(level.bgm)
    pygame.mixer.music.play(-1)

    count = 0
    bossMode = False
    bossDead = False
    warningMode = False

    mapScreen = pygame.Surface((screen.get_width() * 3//4, screen.get_height() * 3//4)).convert_alpha()
    mapScreen.fill(BLUE)
    mapScreen.set_colorkey(BLUE)
    mapRect = mapScreen.get_rect()

    tmp1 = Text("Weak spots to target", subtitle, WHITE)
    tip1 = Text("HINT: Go after its limbs", subtitle, WHITE)

    tmp1.rect.midbottom = mapRect.midtop
    prema.map_rect.midtop = tmp1.rect.midtop
    tip1.rect.midtop = prema.map_rect.midbottom

    mapScreen.blit(prema.weakspot_map, prema.map_rect)
    mapScreen.blit(tmp1.image, tmp1.rect)
    mapScreen.blit(tip1.image, tip1.rect)

    mapRect.center = screen.get_rect().center

    miniboss_grp = {}

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if bossDead and event.key == K_RETURN:
                    count = FPS*41
                    break


        playerPoints = Text(str(p1.points), pointFont, WHITE, shadow=True)
        playerPoints.rect.midtop = pointsTitle.rect.midbottom

        if not bossMode and not level.pause:
            if count % level.waveTime == 0 and count > 0:
                level.waveIndex += 1
                if level.waveIndex > len(level.wave) - 1:
                    if not warningMode:
                        warningMode = True
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()

                        pygame.mixer.music.load(level.bossBGM)
                        pygame.mixer.music.play(-1)

                        count = 0
                        level.waveIndex = 0

            if count % (FPS * 8) == 0 and not warningMode:
                wave = level.wave[level.waveIndex]

                for sporeObj in wave:
                    if sporeObj == Premature_2:
                        if not miniboss_grp.get(level.waveIndex):
                            spore = sporeObj(p1, level=level)
                            level.pause = True

                            miniboss_grp[level.waveIndex] = [spore]

                            sporeGroup.add(spore.body)
                            for i in (spore.lig_left + spore.lig_right):
                                sporeGroup.add(i)
                    else:
                        spore = sporeObj(p1)
                        sporeGroup.add(spore)
                        allSprites.add(spore)

            if count % (7 * FPS) == 0:
                tmp = powerUpTypes[random.randint(0, len(powerUpTypes)-1)]
                pUp = tmp() if tmp != WingUp else tmp(p1)

                if len(wingmanGroup.sprites()) and isinstance(pUp, WingUp):
                    continue

                if not pygame.sprite.spritecollideany(pUp, powerUpGroup):
                    powerUpGroup.add(pUp)
        else:
            if prema.body.health <= 0 and not bossDead:
                pygame.mixer.music.load("BGM/complete.ogg")
                pygame.mixer.music.play()

                exp = Explosion(explosion, 3, 0.25, prema.body.rect.center, False, "SFX/ship-explosion.wav")
                bgGroup.add(exp)

                for spore in sporeGroup.sprites():
                    spore.kill()

                bossDead = True
                count = 0
                prema.body.health = 0
                prema.body.kill()

        # To ensure less lag, kill unnecessary sprites.
        if len(fireGroup.sprites()) > 30:
            fireGroup.sprites()[0].kill()

        if len(playerGroup.sprites()) <= 0:
            if p1.lives > 0:
                for sprite in sporeGroup.sprites():
                    if hasattr(sprite, "health"):
                        sprite.health -= 50
                    if hasattr(sprite, "premature"):
                        if not sprite.invincible:
                            sprite.health -= 5
                            sprite.premature.health -= 5
                p1.rect.midbottom = screen.get_rect().midbottom
                p1.bombs = 5
                playerGroup.add(p1)
                allSprites.add(p1)
            else:
                for sprite in sporeGroup.sprites():
                    sprite.kill()
                for sprite in allSprites.sprites():
                    sprite.kill()
                for sprite in healthBarGroup.sprites():
                    sprite.kill()
                for sprite in playerGroup.sprites():
                    sprite.kill()
                for sprite in allClouds.sprites():
                    sprite.kill()

                gameOver()


        if bossDead and count > FPS*41:
            fadeScreen(screen, True)
            p1.health = p1.maxHealth
            p1.lives = 3
            p1.bombs = 5

            for sprite in sporeGroup.sprites():
                sprite.kill()
            for sprite in allSprites.sprites():
                sprite.kill()
            for sprite in healthBarGroup.sprites():
                sprite.kill()
            for sprite in playerGroup.sprites():
                sprite.kill()
            for sprite in allClouds.sprites():
                sprite.kill()

            if p1.levelIndex < len(levels) - 1:
                briefingRoom(p1, True)
            else:
                creditsScreen(p1)
            exit()

        level.update()
        playerGroup.update()
        fireGroup.update()
        bgGroup.update()
        allClouds.update(speed=level.speed+1)
        healthBarGroup.update()
        if bossMode:
            bossBar.rect.topright = screen.get_rect().topright
        wingmanGroup.update()
        powerUpGroup.update()

        if miniboss_grp.get(level.waveIndex):
            for item in miniboss_grp[level.waveIndex]:
                if isinstance(item, Premature_2):
                    if item.health <= 0:
                        count = level.waveTime - FPS * 5
                        miniboss_grp[level.waveIndex].remove(item)
                        miniboss_grp[level.waveIndex].append(12)
                    item.update()


        if bossMode:
            if not bossDead:
                prema.update(type=level.boss_lazer2)
        # Putting sporeGroup.update() after prema.update() to avoid bugs during boss fight.
        sporeGroup.update()


        screen.fill(BLACK)
        screen.blit(level.image, level.rect)

        cloudsGroup2.draw(screen)

        if not bossMode or bossDead:
            fireGroup.draw(screen)

        playerGroup.draw(screen)

        if not bossDead:
            sporeGroup.draw(screen)

            if miniboss_grp.get(level.waveIndex):
                for item in miniboss_grp[level.waveIndex]:
                    if isinstance(item, Premature_2):
                        item.draw_gun(screen)

            if bossMode:
                fireGroup.draw(screen)
                prema.draw_gun(screen)

        cloudsGroup1.draw(screen)
        wingmanGroup.draw(screen)
        powerUpGroup.draw(screen)
        healthBarGroup.draw(screen)

        # printing players points
        screen.blit(pointsTitle.image, pointsTitle.rect)
        screen.blit(playerPoints.image, playerPoints.rect)


        # Printing players number of lives and number of bombs using icons.
        p1.printLifeCount()
        p1.printBombCount()

        if warningMode:
            for sprite in powerUpGroup.sprites():
                sprite.kill()

            if level.speed <= level.boss_speed:
                level.speed += 2/FPS
            elif level.speed >= level.boss_speed:
                level.speed -= 2 / FPS

            for sprite in sporeGroup.sprites():
                sprite.kill()

            screen.blit(shade_layer, (0, 0))
            if count < FPS*6:
                screen.blit(warning.image, warning.rect)
                warning.blink()
            else:
                screen.blit(mapScreen, mapRect)

            if count > FPS*11:
                healthBarGroup.add(bossBar)

                sporeGroup.add(prema.body)
                for left in prema.lig_left:
                    sporeGroup.add(left)
                for right in prema.lig_right:
                    sporeGroup.add(right)

                count = 0
                bossMode = True
                warningMode = False

        if bossDead:
            if level.speed < 40:
                level.speed += 2/FPS

            screen.blit(winText.image, winText.rect)
            screen.blit(sideMsg.image, sideMsg.rect)

        drawScanlines(1, 50, screen)

        pygame.display.update()
        clock.tick(FPS)
        count += 1

startScreen()