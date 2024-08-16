#include <stdio.h>
#include "pico/stdlib.h"

int uart_gets(uart_inst_t *uart, char *output) {
  int length = 0; // Keep track of how many bytes were read
  while (uart_is_readable(uart)) {
    output[length++] = uart_getc(uart);
  }
  if (length > 0) {
    output[length] = 0; // Null terminator
  }
  return length;
}

int main() {
  // Initialise USB serial
  stdio_init_all();
  printf("Booted\n");

  // Enable the onboard LED to show the code has uploaded
  const uint LED_PIN = PICO_DEFAULT_LED_PIN;
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);
  gpio_put(LED_PIN, 1);

  // Configure UART1
  int baud = 115200;
  int rx_pin = 5;
  int tx_pin = 4;
  uart_init(uart1, baud);
  gpio_set_function(rx_pin, GPIO_FUNC_UART);
  gpio_set_function(tx_pin, GPIO_FUNC_UART);

  printf("Sleeping...\n");
  sleep_ms(2000);
  printf("UART1 Passthrough (baud=%i, RX=GP%i, TX=GP%i)\n", baud, rx_pin, tx_pin);

  char buffer[2048];

  while (true) {
    // Check if we are sending anything to the radio
    int outgoing = getchar_timeout_us(0);
    if (outgoing && outgoing != PICO_ERROR_TIMEOUT) {
      uart_puts(uart1, buffer); // Send buffer to radio
    }

    // Check if the radio has sent us any data
    if (uart_gets(uart1, buffer)) {
      printf("%s", buffer);
    }
  }
  
  // This should never be reached 
  return 0;
}


