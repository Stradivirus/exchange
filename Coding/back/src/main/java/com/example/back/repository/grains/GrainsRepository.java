package com.example.back.repository.grains;

import com.example.back.entity.grains.Grains;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface GrainsRepository extends JpaRepository<Grains, LocalDate> {
    List<Grains> findTop30ByOrderByDateDesc();
}