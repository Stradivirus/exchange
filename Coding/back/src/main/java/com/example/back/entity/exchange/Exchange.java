package com.example.back.entity.exchange;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;

@Entity
@Table(name = "exchange")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Exchange {

    @Id
    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Column(name = "usd")
    private Double usd;

    @Column(name = "jpy")
    private Double jpy;

    @Column(name = "eur")
    private Double eur;

    @Column(name = "cny")
    private Double cny;
}