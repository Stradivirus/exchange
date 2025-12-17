package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List; // 필수 추가

public interface CornRepository extends MongoRepository<Corn, String> {
    Corn findTopByOrderByDateDesc();

    List<Corn> findTop30ByOrderByDateDesc();
}
