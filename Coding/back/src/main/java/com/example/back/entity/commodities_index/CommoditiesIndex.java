package com.example.back.entity.commodities_index;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;

@Entity
@Table(name = "commodities_index")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CommoditiesIndex {
    @Id
    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Column(name = "dxy")
    private Double dxy;

    @Column(name = "vix")
    private Double vix;
}