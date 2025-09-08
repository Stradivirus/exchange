package com.example.back.entity.commodities;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;

@Entity
@Table(name = "commodities")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Commodities {
    @Id
    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Column(name = "gold")
    private Double gold;

    @Column(name = "gold_volume")
    private Double goldVolume;

    @Column(name = "silver")
    private Double silver;

    @Column(name = "silver_volume")
    private Double silverVolume;

    @Column(name = "copper")
    private Double copper;

    @Column(name = "copper_volume")
    private Double copperVolume;

    @Column(name = "crude_oil")
    private Double crudeOil;

    @Column(name = "crude_oil_volume")
    private Double crudeOilVolume;

    @Column(name = "brent_oil")
    private Double brentOil;

    @Column(name = "brent_oil_volume")
    private Double brentOilVolume;
}