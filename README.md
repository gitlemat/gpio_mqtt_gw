# Por si no se usa dockerhub:

/orangepi_PC_gpio_pyH3-master/pyA20/spi$ vi spi_lib.c
Aqui cambiar #include <sys/ioctl.h> por #include <asm/ioctl.h> 
sudo docker build -t gpio_mqtt_gw .
sudo docker ps -a
sudo docker images

# El docker necesita estos volumes:
# (el config se copia del que está en github. No lo incluye la imagen)

config
logs