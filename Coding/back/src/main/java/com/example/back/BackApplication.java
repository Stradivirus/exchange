package com.example.back;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import me.paulschwarz.springdotenv.DotenvPropertySource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.StandardEnvironment;

import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoClient;

import java.sql.Connection;
import java.sql.DriverManager;

@SpringBootApplication
public class BackApplication implements org.springframework.boot.CommandLineRunner {

    @Value("${MONGO_URI}")
    private String mongoUri;

    @Value("${PG_HOST}")
    private String pgHost;

    @Value("${PG_DB}")
    private String pgDb;

    @Value("${PG_USER}")
    private String pgUser;

    @Value("${PG_PASSWORD}")
    private String pgPassword;

    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(BackApplication.class);
        ConfigurableEnvironment environment = new StandardEnvironment();
        DotenvPropertySource.addToEnvironment(environment);
        app.setEnvironment(environment);
        app.run(args);
    }

    public void testMongoConnection() {
        try (MongoClient mongoClient = MongoClients.create(mongoUri)) {
            mongoClient.listDatabaseNames().first();
            System.out.println("MongoDB 연결 성공");
        } catch (Exception e) {
            System.out.println("MongoDB 연결 실패: " + e.getMessage());
        }
    }

    public void testPostgresConnection() {
        String url = "jdbc:postgresql://" + pgHost + ":5432/" + pgDb;
        try (Connection conn = DriverManager.getConnection(url, pgUser, pgPassword)) {
            if (conn != null && !conn.isClosed()) {
                System.out.println("PostgreSQL 연결 성공");
            }
        } catch (Exception e) {
            System.out.println("PostgreSQL 연결 실패: " + e.getMessage());
        }
    }

    @Override
    public void run(String... args) {
        testMongoConnection();
        testPostgresConnection();
    }
}