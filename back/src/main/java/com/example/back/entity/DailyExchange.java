package com.example.back.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;

@Entity
@Table(name = "daily_exchange")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DailyExchange {
    @Id
    @Column(name = "date")
    private LocalDate date;

    private Double dollar;
    private Double gold;
    private Double oil;
    private Double dxy;
    @Column(name = "base_rate")
    private Double baseRate;
    @Column(name = "us_base_rate")
    private Double usBaseRate;
}
