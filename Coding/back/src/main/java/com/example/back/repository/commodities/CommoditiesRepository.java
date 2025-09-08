package com.example.back.repository.commodities;

import com.example.back.entity.commodities.Commodities;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface CommoditiesRepository extends JpaRepository<Commodities, LocalDate> {
    List<Commodities> findTop30ByOrderByDateDesc();
}