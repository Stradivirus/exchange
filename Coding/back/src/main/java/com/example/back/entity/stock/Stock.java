package com.example.back.entity.stock;

import jakarta.persistence.*;
import lombok.*;
import java.sql.Date;

@Entity
@Table(name = "stock")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Stock {
    @Id
    @Column(name = "date", nullable = false)
    private Date date;

    @Column(name = "sp500")
    private Double sp500;

    @Column(name = "sp500_volume")
    private Double sp500Volume;

    @Column(name = "dow_jones")
    private Double dowJones;

    @Column(name = "dow_jones_volume")
    private Double dowJonesVolume;

    @Column(name = "nasdaq")
    private Double nasdaq;

    @Column(name = "nasdaq_volume")
    private Double nasdaqVolume;

    @Column(name = "kospi")
    private Double kospi;

    @Column(name = "kospi_volume")
    private Double kospiVolume;

    @Column(name = "kosdaq")
    private Double kosdaq;

    @Column(name = "kosdaq_volume")
    private Double kosdaqVolume;
}
