package ai.openclaw.ocjbot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class OcjbotApplication {

    public static void main(String[] args) {
        SpringApplication.run(OcjbotApplication.class, args);
    }
}