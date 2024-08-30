/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LORA_M0_Pin GPIO_PIN_0
#define LORA_M0_GPIO_Port GPIOA
#define LORA_M1_Pin GPIO_PIN_1
#define LORA_M1_GPIO_Port GPIOA
#define LORA_AUX_Pin GPIO_PIN_4
#define LORA_AUX_GPIO_Port GPIOA
#define BTN1_Pin GPIO_PIN_5
#define BTN1_GPIO_Port GPIOA
#define BTN1_EXTI_IRQn EXTI9_5_IRQn
#define BTN2_Pin GPIO_PIN_6
#define BTN2_GPIO_Port GPIOA
#define BTN2_EXTI_IRQn EXTI9_5_IRQn
#define BTN3_Pin GPIO_PIN_7
#define BTN3_GPIO_Port GPIOA
#define BTN3_EXTI_IRQn EXTI9_5_IRQn
#define BTN4_Pin GPIO_PIN_0
#define BTN4_GPIO_Port GPIOB
#define BTN4_EXTI_IRQn EXTI0_IRQn
#define BTN5_Pin GPIO_PIN_1
#define BTN5_GPIO_Port GPIOB
#define BTN5_EXTI_IRQn EXTI1_IRQn
#define STOP_LED_Pin GPIO_PIN_13
#define STOP_LED_GPIO_Port GPIOB
#define GPS_LED_Pin GPIO_PIN_14
#define GPS_LED_GPIO_Port GPIOB
#define LAMP2_Pin GPIO_PIN_11
#define LAMP2_GPIO_Port GPIOA
#define LAMP1_Pin GPIO_PIN_12
#define LAMP1_GPIO_Port GPIOA
#define MODE_SLCT_Pin GPIO_PIN_15
#define MODE_SLCT_GPIO_Port GPIOA
#define BUZZER_Pin GPIO_PIN_8
#define BUZZER_GPIO_Port GPIOB
#define DBG_LED_Pin GPIO_PIN_9
#define DBG_LED_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
