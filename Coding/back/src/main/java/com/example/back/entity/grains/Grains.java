package com.example.back.entity.grains;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;

@Entity
@Table(name = "grains")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Grains {
    @Id
    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Column(name = "corn")
    private Double corn;

    @Column(name = "corn_volume")
    private Double cornVolume;

    @Column(name = "wheat")
    private Double wheat;

    @Column(name = "wheat_volume")
    private Double wheatVolume;

    @Column(name = "rice")
    private Double rice;

    @Column(name = "rice_volume")
    private Double riceVolume;

    @Column(name = "coffee")
    private Double coffee;

    @Column(name = "coffee_volume")
    private Double coffeeVolume;

    @Column(name = "sugar")
    private Double sugar;

    @Column(name = "sugar_volume")
    private Double sugarVolume;
}