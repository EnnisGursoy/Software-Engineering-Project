-- MySQL dump 10.13  Distrib 5.7.24, for osx11.1 (x86_64)
--
-- Host: localhost    Database: payroll_system
-- ------------------------------------------------------
-- Server version	9.6.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup
--

SET @@GLOBAL.GTID_PURGED='1a7b67ec-05c8-11f1-82d4-e33661484379:1-28';

--
-- Table structure for table `departments`
--

DROP TABLE IF EXISTS `departments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `departments` (
  `department_id` int NOT NULL AUTO_INCREMENT,
  `department_name` varchar(100) NOT NULL,
  `manager_id` int DEFAULT NULL,
  `manager_user_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`department_id`),
  KEY `manager_id` (`manager_id`),
  KEY `manager_user_id` (`manager_user_id`),
  CONSTRAINT `departments_ibfk_1` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`employee_id`),
  CONSTRAINT `departments_ibfk_2` FOREIGN KEY (`manager_user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `departments`
--

LOCK TABLES `departments` WRITE;
/*!40000 ALTER TABLE `departments` DISABLE KEYS */;
INSERT INTO `departments` VALUES (1,'Engineering',NULL,'2026-02-09 15:29:22'),(2,'Sales',NULL,'2026-02-09 15:29:22'),(3,'Human Resources',NULL,'2026-02-09 15:29:22'),(4,'Marketing',NULL,'2026-02-09 15:29:22');
/*!40000 ALTER TABLE `departments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employee_positions`
--

DROP TABLE IF EXISTS `employee_positions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `employee_positions` (
  `emp_position_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `position_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  `current_salary` decimal(10,2) DEFAULT NULL,
  `current_hourly_rate` decimal(8,2) DEFAULT NULL,
  `pay_frequency` enum('weekly','bi_weekly','semi_monthly','monthly') NOT NULL,
  `is_current` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`emp_position_id`),
  KEY `employee_id` (`employee_id`),
  KEY `position_id` (`position_id`),
  CONSTRAINT `employee_positions_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`),
  CONSTRAINT `employee_positions_ibfk_2` FOREIGN KEY (`position_id`) REFERENCES `positions` (`position_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employee_positions`
--

LOCK TABLES `employee_positions` WRITE;
/*!40000 ALTER TABLE `employee_positions` DISABLE KEYS */;
INSERT INTO `employee_positions` VALUES (1,1,1,'2023-01-10',NULL,85000.00,NULL,'bi_weekly',1,'2026-02-09 15:29:33'),(2,2,3,'2022-06-15',NULL,NULL,25.00,'bi_weekly',1,'2026-02-09 15:29:33'),(3,3,2,'2024-02-01',NULL,120000.00,NULL,'bi_weekly',1,'2026-02-09 15:29:33'),(4,4,4,'2023-05-20',NULL,75000.00,NULL,'semi_monthly',1,'2026-02-09 15:29:33'),(5,5,5,'2021-03-15',NULL,NULL,22.50,'bi_weekly',1,'2026-02-09 15:29:33');
/*!40000 ALTER TABLE `employee_positions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employees`
--

DROP TABLE IF EXISTS `employees`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `employees` (
  `employee_id` int NOT NULL AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `city` varchar(50) DEFAULT NULL,
  `state` varchar(50) DEFAULT NULL,
  `zip_code` varchar(10) DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `hire_date` date NOT NULL,
  `termination_date` date DEFAULT NULL,
  `ssn` varchar(11) DEFAULT NULL,
  `employment_status` enum('active','terminated','on_leave') DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`employee_id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `ssn` (`ssn`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employees`
--

LOCK TABLES `employees` WRITE;
/*!40000 ALTER TABLE `employees` DISABLE KEYS */;
INSERT INTO `employees` VALUES (1,'John','Doe','john.doe@company.com','555-0101','123 Main St','New York','NY','10001','1990-05-15','2023-01-10',NULL,'123-45-6789','active','2026-02-09 15:29:25','2026-02-09 15:29:25'),(2,'Jane','Smith','jane.smith@company.com','555-0102','456 Oak Ave','Los Angeles','CA','90001','1988-08-22','2022-06-15',NULL,'987-65-4321','active','2026-02-09 15:29:25','2026-02-09 15:29:25'),(3,'Mike','Johnson','mike.j@company.com','555-0103','789 Pine Rd','Chicago','IL','60601','1995-03-30','2024-02-01',NULL,'456-78-9012','active','2026-02-09 15:29:25','2026-02-09 15:29:25'),(4,'Sarah','Williams','sarah.w@company.com','555-0104','321 Elm St','Houston','TX','77001','1992-11-12','2023-05-20',NULL,'234-56-7890','active','2026-02-09 15:29:25','2026-02-09 15:29:25'),(5,'David','Brown','david.b@company.com','555-0105','654 Maple Dr','Phoenix','AZ','85001','1985-07-08','2021-03-15',NULL,'345-67-8901','active','2026-02-09 15:29:25','2026-02-09 15:29:25');
/*!40000 ALTER TABLE `employees` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pay_periods`
--

DROP TABLE IF EXISTS `pay_periods`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pay_periods` (
  `pay_period_id` int NOT NULL AUTO_INCREMENT,
  `period_start_date` date NOT NULL,
  `period_end_date` date NOT NULL,
  `pay_date` date NOT NULL,
  `period_type` enum('weekly','bi_weekly','semi_monthly','monthly') NOT NULL,
  `status` enum('open','processing','paid','closed') DEFAULT 'open',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pay_period_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pay_periods`
--

LOCK TABLES `pay_periods` WRITE;
/*!40000 ALTER TABLE `pay_periods` DISABLE KEYS */;
INSERT INTO `pay_periods` VALUES (1,'2026-01-20','2026-02-02','2026-02-07','bi_weekly','paid','2026-02-09 15:29:52'),(2,'2026-02-03','2026-02-16','2026-02-21','bi_weekly','open','2026-02-09 15:29:52'),(3,'2026-02-17','2026-03-02','2026-03-07','bi_weekly','open','2026-02-09 15:29:52');
/*!40000 ALTER TABLE `pay_periods` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `paychecks`
--

DROP TABLE IF EXISTS `paychecks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `paychecks` (
  `paycheck_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `pay_period_id` int NOT NULL,
  `check_number` varchar(50) DEFAULT NULL,
  `gross_pay` decimal(10,2) NOT NULL,
  `net_pay` decimal(10,2) NOT NULL,
  `federal_tax` decimal(10,2) DEFAULT '0.00',
  `state_tax` decimal(10,2) DEFAULT '0.00',
  `social_security` decimal(10,2) DEFAULT '0.00',
  `medicare` decimal(10,2) DEFAULT '0.00',
  `health_insurance` decimal(10,2) DEFAULT '0.00',
  `retirement_401k` decimal(10,2) DEFAULT '0.00',
  `other_deductions` decimal(10,2) DEFAULT '0.00',
  `payment_method` enum('direct_deposit','check','cash') DEFAULT 'direct_deposit',
  `payment_status` enum('pending','processed','paid','void') DEFAULT 'pending',
  `payment_date` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`paycheck_id`),
  KEY `employee_id` (`employee_id`),
  KEY `pay_period_id` (`pay_period_id`),
  CONSTRAINT `paychecks_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`),
  CONSTRAINT `paychecks_ibfk_2` FOREIGN KEY (`pay_period_id`) REFERENCES `pay_periods` (`pay_period_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `paychecks`
--

LOCK TABLES `paychecks` WRITE;
/*!40000 ALTER TABLE `paychecks` DISABLE KEYS */;
/*!40000 ALTER TABLE `paychecks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `positions`
--

DROP TABLE IF EXISTS `positions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `positions` (
  `position_id` int NOT NULL AUTO_INCREMENT,
  `position_title` varchar(100) NOT NULL,
  `department_id` int DEFAULT NULL,
  `base_salary` decimal(10,2) DEFAULT NULL,
  `hourly_rate` decimal(8,2) DEFAULT NULL,
  `employment_type` enum('full_time','part_time','contract') NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`position_id`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `positions_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`department_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `positions`
--

LOCK TABLES `positions` WRITE;
/*!40000 ALTER TABLE `positions` DISABLE KEYS */;
INSERT INTO `positions` VALUES (1,'Software Engineer',1,85000.00,NULL,'full_time','2026-02-09 15:29:29'),(2,'Senior Software Engineer',1,120000.00,NULL,'full_time','2026-02-09 15:29:29'),(3,'Sales Representative',2,NULL,25.00,'full_time','2026-02-09 15:29:29'),(4,'HR Manager',3,75000.00,NULL,'full_time','2026-02-09 15:29:29'),(5,'Marketing Coordinator',4,NULL,22.50,'full_time','2026-02-09 15:29:29');
/*!40000 ALTER TABLE `positions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tax_information`
--

DROP TABLE IF EXISTS `tax_information`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tax_information` (
  `tax_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `filing_status` enum('single','married','head_of_household') NOT NULL,
  `federal_allowances` int DEFAULT '0',
  `state_allowances` int DEFAULT '0',
  `additional_withholding` decimal(8,2) DEFAULT '0.00',
  `exempt_federal` tinyint(1) DEFAULT '0',
  `exempt_state` tinyint(1) DEFAULT '0',
  `effective_date` date NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`tax_id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `tax_information_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tax_information`
--

LOCK TABLES `tax_information` WRITE;
/*!40000 ALTER TABLE `tax_information` DISABLE KEYS */;
INSERT INTO `tax_information` VALUES (1,1,'single',1,1,0.00,0,0,'2023-01-10','2026-02-09 15:29:36'),(2,2,'married',2,2,50.00,0,0,'2022-06-15','2026-02-09 15:29:36'),(3,3,'married',2,2,0.00,0,0,'2024-02-01','2026-02-09 15:29:36'),(4,4,'single',1,1,25.00,0,0,'2023-05-20','2026-02-09 15:29:36'),(5,5,'head_of_household',1,1,0.00,0,0,'2021-03-15','2026-02-09 15:29:36');
/*!40000 ALTER TABLE `tax_information` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `time_entries`
--

DROP TABLE IF EXISTS `time_entries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `time_entries` (
  `entry_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `entry_date` date NOT NULL,
  `clock_in` time DEFAULT NULL,
  `clock_out` time DEFAULT NULL,
  `regular_hours` decimal(5,2) DEFAULT '0.00',
  `overtime_hours` decimal(5,2) DEFAULT '0.00',
  `entry_type` enum('work','sick','vacation','holiday','unpaid') DEFAULT 'work',
  `notes` text,
  `approved` tinyint(1) DEFAULT '0',
  `approved_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`entry_id`),
  KEY `employee_id` (`employee_id`),
  KEY `approved_by` (`approved_by`),
  CONSTRAINT `time_entries_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`),
  CONSTRAINT `time_entries_ibfk_2` FOREIGN KEY (`approved_by`) REFERENCES `employees` (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `time_entries`
--

LOCK TABLES `time_entries` WRITE;
/*!40000 ALTER TABLE `time_entries` DISABLE KEYS */;
INSERT INTO `time_entries` VALUES (1,1,'2026-02-03','09:00:00','17:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(2,1,'2026-02-04','09:00:00','17:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(3,1,'2026-02-05','09:00:00','17:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(4,1,'2026-02-06','09:00:00','18:00:00',8.00,1.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(5,1,'2026-02-07','09:00:00','17:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(6,2,'2026-02-03','08:00:00','16:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(7,2,'2026-02-04','08:00:00','16:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(8,2,'2026-02-05','08:00:00','16:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(9,2,'2026-02-06','08:00:00','17:00:00',8.00,1.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(10,2,'2026-02-07','08:00:00','16:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(11,3,'2026-02-03','09:00:00','17:30:00',8.00,0.50,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(12,3,'2026-02-04','09:00:00','18:00:00',8.00,1.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(13,3,'2026-02-05','09:00:00','17:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(14,3,'2026-02-06','09:00:00','19:00:00',8.00,2.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(15,3,'2026-02-07','09:00:00','17:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(16,4,'2026-02-03','08:30:00','16:30:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(17,4,'2026-02-04','08:30:00','16:30:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(18,4,'2026-02-05','08:30:00','16:30:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(19,4,'2026-02-06',NULL,NULL,0.00,0.00,'sick',NULL,1,NULL,'2026-02-09 15:29:48'),(20,4,'2026-02-07','08:30:00','16:30:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(21,5,'2026-02-03','10:00:00','18:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(22,5,'2026-02-04','10:00:00','18:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(23,5,'2026-02-05','10:00:00','18:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(24,5,'2026-02-06','10:00:00','18:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48'),(25,5,'2026-02-07','10:00:00','18:00:00',8.00,0.00,'work',NULL,1,NULL,'2026-02-09 15:29:48');
/*!40000 ALTER TABLE `time_entries` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-09 10:38:11
